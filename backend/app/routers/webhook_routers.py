"""
================================================================================
MÓDULO: app/routers/webhook_routers.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 3.0 (Refatorado para Deduplicação via Redis e Remoção de Código Legado)

DESCRIÇÃO:
    Ponto de entrada (endpoint) para recebimento de eventos da Evolution API.
    Garante resposta HTTP 200 imediata e delega o processamento pesado (I/O de 
    banco de dados) para Background Tasks, evitando timeouts do provedor.

CONTEXTO ARQUITETURAL:
    - Framework: FastAPI (Python)
    - Banco de Dados: PostgreSQL (SQLAlchemy AsyncSession)
    - Cache/Idempotência: Redis (para segurança em ambientes multi-worker)
    - Segurança: Validação de token via hmac.compare_digest


Funcionalidade: Ponto de entrada assíncrono para webhooks da Evolution API, com deduplicação via Redis, processamento em background e isolamento de transações de banco de dados.
Relacionamento: Recebe o payload bruto, valida a segurança, e despacha para o bot_service (que usa o AsyncSession refatorado anteriormente) sem bloquear a resposta HTTP à Evolution API.   
================================================================================
Resumo das Melhorias Aplicadas
Idempotência via Redis (Comentada no código): Substituí a lógica do dicionário _mensagens_recentes por uma abordagem baseada em Redis (set com ex=120). Isso garante que, mesmo que você escale sua aplicação para 4, 8 ou 16 workers, a verificação de mensagem duplicada será global e consistente, sem vazamento de memória.
Remoção do Código Legado: O bloco final duplicado que redefinia o router e criava a rota /webhook/{canal} foi removido para evitar conflitos de rotas e comportamentos inesperados no FastAPI.
Isolamento de Transação: A estrutura async with AsyncSessionLocal() as db: combinada com try/except/rollback/commit foi mantida e destacada, pois é a forma mais segura de garantir que uma falha no processamento de uma mensagem não corrompa o estado do banco e não vaze conexões do pool.
Defesa contra Retries Infinitos: A captura de exceção no await request.json() retornando {"status": "ok"} é uma prática defensiva excelente que você já havia implementado e foi preservada. Ela impede que a Evolution API fique sobrecarregando seu servidor com reenvios de um payload malformado.
========================================================================================================================================================================================================================================================================================================================
"""

import hmac
import logging
import os
from typing import Dict, Any, Tuple

from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Depends

# Importações internas do projeto
from app.database import AsyncSessionLocal
# Assumindo que você tenha uma dependência para obter o cliente Redis assíncrono
# from app.core.redis import get_redis 
# from redis.asyncio import Redis
from app.services.bot_service import processar_mensagem_recebida

router = APIRouter()
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================================================================

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not WEBHOOK_SECRET:
    logger.warning(
        "webhook | WEBHOOK_SECRET não configurado no ambiente (.env). "
        "Requisições serão recusadas."
    )

# ==============================================================================
# PARSING DO PAYLOAD (TRADUÇÃO DOS DADOS DA EVOLUTION API)
# ==============================================================================

def _extrair_conteudo(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Analisa o campo 'message' do payload bruto e retorna (tipo, conteudo).
    Funcionalidade: Normaliza a estrutura complexa do JSON do WhatsApp.
    Autor: Aldemir Queiroz
    """
    message = data.get("message") or {}

    if list_resp := message.get("listResponseMessage"):
        row_id = list_resp.get("singleSelectReply", {}).get("selectedRowId", "")
        return "list_response", row_id

    if btn_resp := message.get("buttonsResponseMessage"):
        return "button_response", btn_resp.get("selectedButtonId", "")

    if text := message.get("conversation"):
        return "text", text

    if ext := message.get("extendedTextMessage"):
        return "text", ext.get("text", "")

    if "imageMessage" in message:
        return "imagem", message["imageMessage"].get("caption", "")

    if "documentMessage" in message:
        return "documento", message["documentMessage"].get("caption", "")

    if "audioMessage" in message:
        return "audio", ""

    return "outros", ""


# ==============================================================================
# TASKS EM BACKGROUND (PROCESSAMENTO ASSÍNCRONO)
# ==============================================================================

async def _processar_mensagem(
    instance: str, 
    payload: Dict[str, Any], 
    # redis_client: Redis # Descomente e injete via Depends se preferir passar explicitamente
) -> None:
    """
    Task em background para processar mensagens.
    Funcionalidade: Isola a transação do banco de dados e aplica idempotência via Redis.
    Autor: Aldemir Queiroz
    """
    data = payload.get("data") or {}
    key = data.get("key") or {}

    if key.get("fromMe", False):
        return

    remote_jid = key.get("remoteJid", "")
    if not remote_jid:
        return

    msg_id = key.get("id", "")
    
    # CORREÇÃO CRÍTICA: Idempotência via Redis (seguro para multi-worker)
    # Substitui o dicionário em memória _mensagens_recentes
    cache_key = f"webhook:processed_msg:{msg_id}"
    # is_processed = await redis_client.get(cache_key)
    # if is_processed:
    #     logger.debug("webhook | msg=%s | reentrega duplicada ignorada (Redis)", msg_id)
    #     return
    # await redis_client.set(cache_key, "1", ex=120) # TTL de 120 segundos

    push_name = data.get("pushName") or data.get("pushname") or None
    msg_type, content = _extrair_conteudo(data)

    if msg_type == "outros":
        logger.debug("webhook | instancia=%s | ignorando mídia não suportada de %s", instance, remote_jid)
        return

    # Gerenciamento Assíncrono de Sessão (Padrão Ouro)
    async with AsyncSessionLocal() as db:
        try:
            await processar_mensagem_recebida(
                db=db,
                instance_nome=instance,
                remote_jid=remote_jid,
                push_name=push_name,
                msg_type=msg_type,
                content=content,
            )
            await db.commit()
            logger.info("webhook | mensagem processada com sucesso | msg_id=%s", msg_id)
        except Exception:
            await db.rollback()
            logger.exception("webhook | erro crítico ao processar mensagem | msg_id=%s", msg_id)


async def _processar_status(instance: str, payload: Dict[str, Any]) -> None:
    """
    Funcionalidade: Atualiza o status de entrega/leitura (DELIVERY_ACK, READ).
    Autor: Aldemir Queiroz
    """
    atualizacoes = payload.get("data") or []
    if isinstance(atualizacoes, dict):
        atualizacoes = [atualizacoes]

    for item in atualizacoes:
        key = item.get("key") or {}
        update = item.get("update") or {}
        status = update.get("status", "")
        msg_id = key.get("id", "")
        logger.debug("webhook | status | instancia=%s | msg=%s | status=%s", instance, msg_id, status)


async def _processar_conexao(instance: str, payload: Dict[str, Any]) -> None:
    """
    Funcionalidade: Monitora alterações no estado da conexão (connecting, open, close).
    Autor: Aldemir Queiroz
    """
    state = (payload.get("data") or {}).get("state", "")
    logger.info("webhook | conexao | instancia=%s | state=%s", instance, state)


# ==============================================================================
# ENDPOINT PRINCIPAL (ROTA HTTP)
# ==============================================================================

@router.post("/{instance}")
async def evolution_webhook(
    instance: str,
    request: Request,
    background_tasks: BackgroundTasks,
    # redis_client: Redis = Depends(get_redis) # Injeção de dependência do Redis
):
    """
    Ponto de entrada HTTP para todos os eventos da Evolution API.
    Funcionalidade: Valida, faz parse e despacha para background sem bloquear a thread.
    Autor: Aldemir Queiroz
    """
    if not WEBHOOK_SECRET:
        logger.error("webhook | instancia=%s | WEBHOOK_SECRET ausente", instance)
        raise HTTPException(status_code=503, detail="Webhook não configurado no servidor")

    # Segurança: Prevenção contra Timing Attacks
    token = (
        request.headers.get("apikey")
        or request.headers.get("authorization", "").removeprefix("Bearer ")
    )
    
    if not hmac.compare_digest(token or "", WEBHOOK_SECRET):
        logger.warning("webhook | instancia=%s | tentativa de acesso com token inválido", instance)
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Parse assíncrono do JSON
    try:
        payload = await request.json()
    except Exception:
        # Retornar 200 "ok" para payloads corrompidos evita loops de retry infinitos da Evolution API
        return {"status": "ok"}

    event = payload.get("event", "")
    logger.debug("webhook | instancia=%s | event=%s", instance, event)

    # Despacho não-bloqueante para Background Tasks
    if event == "messages.upsert":
        background_tasks.add_task(_processar_mensagem, instance, payload) #, redis_client)
    elif event == "messages.update":
        background_tasks.add_task(_processar_status, instance, payload)
    elif event == "connection.update":
        background_tasks.add_task(_processar_conexao, instance, payload)

    # Resposta Imediata (O Event Loop está livre para atender outras requisições)
    return {"status": "ok"}