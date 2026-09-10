"""
app/routers/webhook.py
──────────────────────────────────────────────────────────────────
Recebe todos os eventos da Evolution API.

Registro em main.py:
    app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhook"])

Configuração na Evolution API (para cada instância):
    URL:    https://seu-dominio.com/api/webhook/{instance}
    Events: MESSAGES_UPSERT, MESSAGES_UPDATE, CONNECTION_UPDATE

Retorna 200 imediatamente após autenticar (WEBHOOK_SECRET obrigatório).
O processamento da mensagem ocorre em background para não travar o webhook.
"""

import hmac
import logging
import os
import time

from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from app.database import SessionLocal
from app.services.bot_service import processar_mensagem_recebida

router = APIRouter()
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not WEBHOOK_SECRET:
    logger.warning(
        "webhook | WEBHOOK_SECRET não configurado — POST /api/webhook/* "
        "será recusado até a variável ser definida no .env."
    )

# ── Deduplicação de entregas repetidas ────────────────────────
# A Evolution API (como a maioria dos provedores de webhook) pode reentregar
# o mesmo evento (ex: timeout na resposta, retry de rede). Sem isso, uma
# mesma mensagem do paciente seria processada duas vezes pela máquina de
# estados, duplicando respostas e podendo até avançar o step indevidamente.
# Cache em memória é suficiente aqui: o cenário real é a redelivery quase
# imediata, não uma reentrega dias depois.
DEDUP_TTL_SEGUNDOS = 120
_mensagens_recentes: dict[str, float] = {}


def _ja_processada(msg_id: str) -> bool:
    """Retorna True se este message_id já foi processado dentro do TTL (e marca como visto)."""
    if not msg_id:
        return False

    agora = time.time()
    limite = agora - DEDUP_TTL_SEGUNDOS
    for antigo_id, visto_em in list(_mensagens_recentes.items()):
        if visto_em < limite:
            del _mensagens_recentes[antigo_id]

    if msg_id in _mensagens_recentes:
        return True

    _mensagens_recentes[msg_id] = agora
    return False


# ══════════════════════════════════════════════════════════════
# Parsing do payload Evolution API
# ══════════════════════════════════════════════════════════════

def _extrair_conteudo(data: dict) -> tuple[str, str]:
    """
    Analisa o campo 'message' do payload e retorna (msg_type, content).

    msg_type:
        "text"            — mensagem de texto simples
        "list_response"   — cliente selecionou opção de sendList
        "button_response" — cliente clicou em botão
        "outros"          — áudio, imagem, sticker, etc. (ignorado)

    content:
        texto livre ou o rowId / buttonId selecionado
    """
    message = data.get("message") or {}

    # Seleção de lista interativa (sendList)
    list_resp = message.get("listResponseMessage") or {}
    if list_resp:
        row_id = (
            list_resp
            .get("singleSelectReply", {})
            .get("selectedRowId", "")
        )
        return "list_response", row_id

    # Clique em botão
    btn_resp = message.get("buttonsResponseMessage") or {}
    if btn_resp:
        btn_id = btn_resp.get("selectedButtonId", "")
        return "button_response", btn_id

    # Texto simples
    text = message.get("conversation", "")
    if text:
        return "text", text

    # Texto estendido (links, menções, formatação rich)
    ext = message.get("extendedTextMessage") or {}
    if ext:
        return "text", ext.get("text", "")

    return "outros", ""


# ══════════════════════════════════════════════════════════════
# Task em background — abre e fecha a própria sessão DB
# ══════════════════════════════════════════════════════════════

async def _processar_mensagem(instance: str, payload: dict) -> None:
    data = payload.get("data") or {}
    key  = data.get("key") or {}

    # Ignorar mensagens enviadas pelo próprio bot
    if key.get("fromMe", False):
        return

    remote_jid = key.get("remoteJid", "")
    if not remote_jid:
        return

    msg_id = key.get("id", "")
    if _ja_processada(msg_id):
        logger.debug("webhook | instancia=%s | msg=%s | reentrega duplicada ignorada", instance, msg_id)
        return

    push_name = data.get("pushName") or data.get("pushname") or None
    msg_type, content = _extrair_conteudo(data)

    if msg_type == "outros":
        logger.debug("webhook | instancia=%s | ignorando tipo não-texto de %s", instance, remote_jid)
        return

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
        logger.exception("webhook | instancia=%s | erro ao processar %s", instance, remote_jid)
    finally:
        db.close()


async def _processar_status(instance: str, payload: dict) -> None:
    """Atualiza status de entrega/leitura (DELIVERY_ACK, READ, PLAYED)."""
    atualizacoes = payload.get("data") or []
    if isinstance(atualizacoes, dict):
        atualizacoes = [atualizacoes]

    for item in atualizacoes:
        key    = item.get("key") or {}
        update = item.get("update") or {}
        status = update.get("status", "")
        msg_id = key.get("id", "")
        logger.debug("webhook | status | instancia=%s | msg=%s | status=%s", instance, msg_id, status)
        # TODO: persistir status na tabela Mensagem quando integrado


async def _processar_conexao(instance: str, payload: dict) -> None:
    state = (payload.get("data") or {}).get("state", "")
    logger.info("webhook | conexao | instancia=%s | state=%s", instance, state)
    # TODO: atualizar StatusInstanciaEnum na tabela Instancia quando integrado


# ══════════════════════════════════════════════════════════════
# Endpoint
# ══════════════════════════════════════════════════════════════

@router.post("/{instance}")
async def evolution_webhook(
    instance: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Ponto de entrada para todos os eventos da Evolution API.

    A Evolution API exige resposta HTTP 200 em até ~5 s.
    Todo o processamento pesado (DB + chamadas à Evolution) acontece
    em background, garantindo retorno imediato.

    Segurança: WEBHOOK_SECRET é obrigatório. Valida o header 'apikey'
    ou 'authorization' enviado pela Evolution API.
    """
    if not WEBHOOK_SECRET:
        logger.error("webhook | instancia=%s | WEBHOOK_SECRET ausente", instance)
        raise HTTPException(status_code=503, detail="Webhook não configurado")

    token = (
        request.headers.get("apikey")
        or request.headers.get("authorization", "").removeprefix("Bearer ")
    )
    if not hmac.compare_digest(token or "", WEBHOOK_SECRET):
        logger.warning("webhook | instancia=%s | token inválido", instance)
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    event = payload.get("event", "")
    logger.debug("webhook | instancia=%s | event=%s", instance, event)

    if event == "messages.upsert":
        background_tasks.add_task(_processar_mensagem, instance, payload)

    elif event == "messages.update":
        background_tasks.add_task(_processar_status, instance, payload)

    elif event == "connection.update":
        background_tasks.add_task(_processar_conexao, instance, payload)

    return {"status": "ok"}
