"""
================================================================================
MÓDULO: app/routers/webhook.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 2.0 (Refatorado para suporte a mídias e documentação didática)

DESCRIÇÃO:
    Ponto de entrada (endpoint) para recebimento de eventos da Evolution API 
    (integração com WhatsApp). Este módulo é responsável por autenticar, 
    validar e despachar eventos de mensagens, status e conexão para processamento 
    em background, garantindo alta disponibilidade e resposta imediata (HTTP 200) 
    à API externa, conforme exigido pelo provedor de webhook.

CONTEXTO ARQUITETURAL:
    - Framework: FastAPI (Python)
    - Banco de Dados: PostgreSQL (via SQLAlchemy e SessionLocal)
    - Padrão de Projeto: Background Tasks (para evitar bloqueio da thread principal 
      e timeouts da Evolution API, que exige resposta em ~5 segundos).
    - Segurança: Validação de token via comparação constante (hmac.compare_digest) 
      para prevenir ataques de temporização (timing attacks), utilizando a 
      variável de ambiente WEBHOOK_SECRET.

PÚBLICO-ALVO DA DOCUMENTAÇÃO:
    Este código foi estruturado com comentários didáticos e tipagem rigorosa 
    para servir como material de estudo, facilitar a depuração (troubleshooting) 
    e permitir que outros desenvolvedores da equipe compreendam o fluxo de dados 
    e possam continuar melhorando a solução com segurança.
================================================================================
"""

import hmac
import logging
import os
import time
from typing import Tuple, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Request, HTTPException

# Importações internas do projeto
from app.database import SessionLocal
from app.services.bot_service import processar_mensagem_recebida

# Inicialização do Router do FastAPI
router = APIRouter()
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA E ESTADO GLOBAL
# ==============================================================================

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not WEBHOOK_SECRET:
    logger.warning(
        "webhook | WEBHOOK_SECRET não configurado no ambiente (.env). "
        "Todas as requisições POST /api/webhook/* serão recusadas até que "
        "a variável seja devidamente definida."
    )

# ── Mecanismo de Deduplicação de Entregas (Idempotência) ──────────────────────
# PROBLEMA: Provedores de webhook (como a Evolution API) frequentemente reenviam 
# o mesmo evento em caso de timeout na resposta ou instabilidade de rede.
# SOLUÇÃO: Um cache em memória (dicionário) que armazena os IDs das mensagens 
# processadas recentemente. Se o mesmo ID chegar dentro do TTL (Time-To-Live), 
# ele é ignorado, evitando duplicidade de respostas do bot ou avanço indevido 
# na máquina de estados do atendimento.
DEDUP_TTL_SEGUNDOS = 120
_mensagens_recentes: Dict[str, float] = {}


def _ja_processada(msg_id: str) -> bool:
    """
    Verifica se uma mensagem já foi processada dentro da janela de tempo (TTL).
    
    Args:
        msg_id (str): O identificador único da mensagem fornecido pela Evolution API.
        
    Returns:
        bool: True se a mensagem já foi processada (deve ser ignorada), False caso contrário.
        
    Nota para desenvolvedores:
        A limpeza das chaves expiradas é feita de forma proativa durante a verificação 
        para evitar que o dicionário cresça indefinidamente e consuma memória do servidor.
    """
    if not msg_id:
        return False

    agora = time.time()
    limite = agora - DEDUP_TTL_SEGUNDOS
    
    # Limpeza eficiente: identifica e remove apenas as entradas expiradas
    ids_expirados = [k for k, v in _mensagens_recentes.items() if v < limite]
    for k in ids_expirados:
        del _mensagens_recentes[k]

    if msg_id in _mensagens_recentes:
        return True

    # Registra o novo ID com o timestamp atual
    _mensagens_recentes[msg_id] = agora
    return False


# ==============================================================================
# PARSING DO PAYLOAD (TRADUÇÃO DOS DADOS DA EVOLUTION API)
# ==============================================================================

def _extrair_conteudo(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Analisa o campo 'message' do payload bruto da Evolution API v2 e retorna 
    uma tupla padronizada: (tipo_da_mensagem, conteudo_extraido).
    
    Esta função atua como um tradutor, normalizando a estrutura complexa e 
    aninhada do JSON do WhatsApp para um formato que o nosso `bot_service` 
    consegue entender facilmente.

    Args:
        data (dict): O dicionário contendo os dados brutos do evento 'messages.upsert'.
        
    Returns:
        tuple[str, str]: 
            - msg_type: "text", "list_response", "button_response", "imagem", 
                        "documento", "audio" ou "outros".
            - content: O texto da mensagem, o ID do botão/lista selecionado ou 
                       a legenda (caption) de mídias.
    """
    message = data.get("message") or {}

    # 1. Seleção de lista interativa (sendList)
    list_resp = message.get("listResponseMessage") or {}
    if list_resp:
        row_id = list_resp.get("singleSelectReply", {}).get("selectedRowId", "")
        return "list_response", row_id

    # 2. Clique em botão de resposta
    btn_resp = message.get("buttonsResponseMessage") or {}
    if btn_resp:
        btn_id = btn_resp.get("selectedButtonId", "")
        return "button_response", btn_id

    # 3. Texto simples (mensagens de texto padrão)
    text = message.get("conversation", "")
    if text:
        return "text", text

    # 4. Texto estendido (contém formatação rich, links, menções @)
    ext = message.get("extendedTextMessage") or {}
    if ext:
        return "text", ext.get("text", "")

    # 5. Imagens (ex: fotos de exames, pedidos médicos digitalizados)
    # Nota: A legenda (caption) é extraída pois o usuário pode enviar instruções junto à imagem.
    if "imageMessage" in message:
        caption = message["imageMessage"].get("caption", "")
        return "imagem", caption

    # 6. Documentos (ex: PDFs de guias médicas, laudos, comprovantes)
    if "documentMessage" in message:
        caption = message["documentMessage"].get("caption", "")
        return "documento", caption

    # 7. Mensagens de Áudio (ex: notas de voz do paciente)
    if "audioMessage" in message:
        return "audio", ""

    # 8. Fallback para mídias não tratadas pelo bot no momento (stickers, reações, localização)
    return "outros", ""


# ==============================================================================
# TASKS EM BACKGROUND (PROCESSAMENTO ASSÍNCRONO)
# ==============================================================================

async def _processar_mensagem(instance: str, payload: Dict[str, Any]) -> None:
    """
    Task em background responsável por processar mensagens recebidas.
    
    Por que usar Background Task?
    O FastAPI retornaria o HTTP 200 apenas após a conclusão desta função. 
    Como ela envolve I/O de banco de dados e possíveis chamadas de rede, 
    delegá-la ao background garante que a Evolution API receba a resposta 
    imediatamente, evitando retransmissões (retries) desnecessárias.
    """
    data = payload.get("data") or {}
    key = data.get("key") or {}

    # Regra de Negócio: Ignorar mensagens enviadas pelo próprio número do bot 
    # para evitar loops infinitos de resposta.
    if key.get("fromMe", False):
        return

    remote_jid = key.get("remoteJid", "")
    if not remote_jid:
        return

    msg_id = key.get("id", "")
    
    # Verificação de idempotência
    if _ja_processada(msg_id):
        logger.debug("webhook | instancia=%s | msg=%s | reentrega duplicada ignorada", instance, msg_id)
        return

    push_name = data.get("pushName") or data.get("pushname") or None
    msg_type, content = _extrair_conteudo(data)

    # Filtro de Mídia: Descarta apenas conteúdos verdadeiramente não suportados.
    # "imagem", "documento" e "audio" agora são permitidos e seguirão para o bot_service.
    if msg_type == "outros":
        logger.debug("webhook | instancia=%s | ignorando tipo de mídia não suportado de %s", instance, remote_jid)
        return

    # Gerenciamento de Sessão de Banco de Dados
    # Cada task em background deve criar e fechar sua própria sessão para evitar 
    # vazamento de conexões (connection leaks) e conflitos de thread.
    db = SessionLocal()
    try:
        await processar_mensagem_recebida(
            db=db,
            instance_nome=instance,
            remote_jid=remote_jid,
            push_name=push_name,
            msg_type=msg_type,
            content=content,
        )
    except Exception:
        # logger.exception já inclui o stack trace completo, essencial para depuração
        logger.exception("webhook | instancia=%s | erro crítico ao processar mensagem de %s", instance, remote_jid)
    finally:
        db.close()


async def _processar_status(instance: str, payload: Dict[str, Any]) -> None:
    """
    Atualiza o status de entrega/leitura das mensagens (ex: DELIVERY_ACK, READ, PLAYED).
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
        
        # TODO (Aldemir): Persistir este status na tabela 'Mensagem' do banco de dados 
        # quando o modelo de dados (ORM) estiver totalmente integrado.


async def _processar_conexao(instance: str, payload: Dict[str, Any]) -> None:
    """
    Monitora alterações no estado da conexão da instância (ex: connecting, open, close).
    Útil para alertas de monitoramento de saúde do bot.
    """
    state = (payload.get("data") or {}).get("state", "")
    logger.info("webhook | conexao | instancia=%s | state=%s", instance, state)
    
    # TODO (Aldemir): Atualizar o campo 'StatusInstanciaEnum' na tabela 'Instancia' 
    # quando integrado, permitindo que o dashboard mostre se o bot está online ou offline.


# ==============================================================================
# ENDPOINT PRINCIPAL (ROTA HTTP)
# ==============================================================================

@router.post("/{instance}")
async def evolution_webhook(
    instance: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Ponto de entrada HTTP para todos os eventos da Evolution API.
    
    Fluxo de Execução:
    1. Valida a presença do WEBHOOK_SECRET.
    2. Autentica a requisição comparando o token do header com o secret (segurança).
    3. Faz o parse do JSON. Se falhar, retorna 200 "ok" para evitar loops de retry da API.
    4. Despacha a task específica para o background com base no tipo de evento.
    5. Retorna HTTP 200 imediatamente.
    """
    # 1. Validação de Configuração
    if not WEBHOOK_SECRET:
        logger.error("webhook | instancia=%s | WEBHOOK_SECRET ausente", instance)
        raise HTTPException(status_code=503, detail="Webhook não configurado no servidor")

    # 2. Autenticação (Prevenção contra Timing Attacks com hmac.compare_digest)
    token = (
        request.headers.get("apikey")
        or request.headers.get("authorization", "").removeprefix("Bearer ")
    )
    
    if not hmac.compare_digest(token or "", WEBHOOK_SECRET):
        logger.warning("webhook | instancia=%s | tentativa de acesso com token inválido", instance)
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 3. Parse do Payload com tratamento de erro robusto
    try:
        payload = await request.json()
    except Exception:
        # Retorna 200 mesmo com payload inválido. Isso é uma prática defensiva: 
        # evita que a Evolution API fique tentando reenviar um payload corrompido infinitamente.
        return {"status": "ok"}

    event = payload.get("event", "")
    logger.debug("webhook | instancia=%s | event=%s", instance, event)

    # 4. Despacho para Background Tasks
    if event == "messages.upsert":
        background_tasks.add_task(_processar_mensagem, instance, payload)
    elif event == "messages.update":
        background_tasks.add_task(_processar_status, instance, payload)
    elif event == "connection.update":
        background_tasks.add_task(_processar_conexao, instance, payload)

    # 5. Resposta Imediata
    return {"status": "ok"}