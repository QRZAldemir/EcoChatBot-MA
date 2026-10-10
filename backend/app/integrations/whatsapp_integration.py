# ==============================================================================
# ARQUIVO.....: meta_cloud_webhook_parser.py
# AUTOR.......: (refatoração para estudo)
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Parser de Webhook Meta Cloud API (Graph API)
# VERSÃO......: 2.1.0 (Correção definitiva - loop infinito + rejeição de caption)
# LINGUAGEM...: Python 3.12+
# ==============================================================================
# DESCRIÇÃO...:
# Parser responsável por interpretar o envelope JSON enviado pela Meta Cloud API
# no endpoint de webhook do WhatsApp Business.
#
# PROBLEMA A CORRIGIR (BUG DE LOOP INFINITO COM EVENTOS "statuses"):
#   A Meta envia, no MESMO envelope, notificações de entrega/leitura em
#   entry[].changes[].value["statuses"]. Se o parser interpretar "statuses"
#   como mensagem recebida, o bot responderá à própria notificação,
#   gerando loop infinito.
#
# CORREÇÃO DEFINITIVA:
#   - Varre TODOS os entries/changes (NUNCA retorna no primeiro change).
#   - Qualquer change que contenha APENAS "statuses" é IGNORADO.
#   - Retorna type="status" APENAS quando NÃO existem mensagens reais em
#     nenhum change do envelope inteiro.
#   - Só processa quando existir "messages" (prioriza mensagem real).
#
# OBS: Este script foca EXCLUSIVAMENTE na correção de parsing do webhook
# da Meta Cloud API (tratamento de "statuses"). Não altera envio de caption
# (isso deve ser tratado no adaptador que efetivamente envia mídia).
# ==============================================================================
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

ParsedEventType = Literal["message", "status", "ignored"]


@dataclass(slots=True)
class ParsedWebhookEvent:
    """Resultado normalizado do parsing de webhook Meta Cloud API."""

    type: ParsedEventType
    chat_id: str | None = None
    text: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_incoming_webhook(payload: dict[str, Any]) -> ParsedWebhookEvent:
    """
    Interpreta envelope JSON da Meta Cloud API.

    REGRA CRÍTICA:
    1. Se houver QUALQUER change com "messages" válido -> retorna a primeira
       mensagem encontrada (processa como message). Nunca retorna "status".
    2. Se NÃO houver mensagens, mas houver ao menos um change com APENAS
       "statuses" (ou statuses presente) -> retorna type="status".
    3. Caso contrário -> "ignored".
    """
    if not isinstance(payload, dict):
        logger.warning("Webhook recebido não é um dict: %r", type(payload))
        return ParsedWebhookEvent(type="ignored", raw=payload or {})

    entries = payload.get("entry") or []
    if not entries:
        logger.debug("Webhook sem 'entry' — ignorando.")
        return ParsedWebhookEvent(type="ignored", raw=payload)

    saw_status_only = False

    for entry in entries:
        for change in (entry.get("changes") or []):
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue

            has_messages = bool(value.get("messages"))
            has_statuses = bool(value.get("statuses"))

            # MENSAGEM REAL existe -> processar imediatamente
            if has_messages:
                messages = value.get("messages") or []
                if not messages:
                    continue
                first_msg = messages[0]
                chat_id = first_msg.get("from") if isinstance(first_msg, dict) else None
                text = _extract_text(first_msg) if isinstance(first_msg, dict) else None
                if not chat_id:
                    logger.warning("Mensagem sem 'from' — ignorando este evento.")
                    continue
                return ParsedWebhookEvent(
                    type="message",
                    chat_id=chat_id,
                    text=text,
                    raw=payload,
                )

            # APENAS status -> marcar e continuar buscando mensagens
            if has_statuses and not has_messages:
                saw_status_only = True
                logger.debug(
                    "Webhook de status recebido (entrega/leitura). "
                    "Ignorado neste change; prosseguindo varredura do envelope."
                )
                continue

    # Fim da varredura: sem mensagens encontradas
    if saw_status_only:
        logger.debug("Envelope contém apenas notificações de status.")
        return ParsedWebhookEvent(type="status", raw=payload)

    logger.debug("Webhook sem 'messages' nem 'statuses' reconhecíveis.")
    return ParsedWebhookEvent(type="ignored", raw=payload)


def _extract_text(message: dict[str, Any]) -> str | None:
    if not isinstance(message, dict):
        return None

    if "text" in message and isinstance(message["text"], dict):
        return message["text"].get("body")

    if "button" in message and isinstance(message["button"], dict):
        return message["button"].get("text")

    if "interactive" in message and isinstance(message["interactive"], dict):
        interactive = message["interactive"]
        if isinstance(interactive.get("button_reply"), dict):
            return interactive["button_reply"].get("title")
        if isinstance(interactive.get("list_reply"), dict):
            return interactive["list_reply"].get("title")

    return None


__all__ = ["ParsedWebhookEvent", "parse_incoming_webhook"]
