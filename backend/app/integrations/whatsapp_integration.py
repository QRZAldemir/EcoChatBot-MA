# ==============================================================================
# ARQUIVO.....: meta_cloud_webhook_parser.py
# AUTOR.......: (refatoração para estudo)
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Parser de Webhook Meta Cloud API (Graph API)
# VERSÃO......: 2.1.1 (Correção definitiva - varredura completa do envelope)
# LINGUAGEM...: Python 3.12+
# ==============================================================================
# DESCRIÇÃO...:
# Parser responsável por interpretar o envelope JSON enviado pela Meta Cloud API
# no endpoint de webhook do WhatsApp Business.
#
# REGRA CRÍTICA (evitar loop infinito com statuses):
#   - Varre TODOS os entries/changes. NUNCA retorna ao encontrar apenas "statuses".
#   - Se existir QUALQUER "messages" não vazio em qualquer change -> retorna
#     a primeira mensagem encontrada (type="message"). Prioriza mensagem real.
#   - Se NÃO houver nenhuma mensagem válida após varrer TODO o envelope,
#     mas houver pelo menos um change com APENAS "statuses" -> retorna type="status".
#   - Caso contrário -> type="ignored".
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

    Regras:
    1. Procura mensagens em TODO o envelope. Ao encontrar a primeira mensagem
       válida (com 'from'), retorna imediatamente type="message".
    2. Enquanto busca, se encontrar changes com APENAS "statuses", marca
       saw_status_only (NÃO retorna). Isso evita perder mensagens que venham
       depois no mesmo envelope.
    3. Se varreu tudo e não encontrou nenhuma mensagem, mas viu pelo menos
       um evento apenas de status -> retorna type="status".
    4. Senão -> type="ignored".
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

            messages = value.get("messages") or []
            statuses = value.get("statuses") or []

            # 1. Prioriza MENSAGEM REAL do cliente
            if messages:
                first_msg = messages[0]
                if isinstance(first_msg, dict):
                    chat_id = first_msg.get("from")
                    if chat_id:
                        text = _extract_text(first_msg)
                        return ParsedWebhookEvent(
                            type="message",
                            chat_id=chat_id,
                            text=text,
                            raw=payload,
                        )
                # Mensagem sem 'from' -> ignora este change e continua varrendo
                continue

            # 2. APENAS status (sem mensagens) -> marcar e NÃO retornar
            if statuses and not messages:
                saw_status_only = True
                logger.debug(
                    "Webhook de status (entrega/leitura) detectado; "
                    "continuando varredura para buscar mensagens."
                )
                continue

    # 3. Varreu todo o envelope sem encontrar nenhuma mensagem válida
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
