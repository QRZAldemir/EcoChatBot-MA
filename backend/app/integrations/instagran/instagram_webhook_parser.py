# ==============================================================================
# ARQUIVO.....: meta_cloud_webhook_parser.py
# AUTOR.......: (refatoração para estudo)
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Parser de Webhook Meta Cloud API (Graph API)
# VERSÃO......: 3.0.0 (Refatoração completa - multi-evento + metadados)
# LINGUAGEM...: Python 3.12+
# ==============================================================================
# DESCRIÇÃO...:
# Parser responsável por interpretar o envelope JSON enviado pela Meta Cloud API
# no endpoint de webhook do WhatsApp Business.
#
# MUDANÇAS EM RELAÇÃO À v2.1.1:
#   1. Retorno alterado de ParsedWebhookEvent único para list[ParsedWebhookEvent].
#      Motivo: a Meta pode agrupar múltiplas mensagens e status no mesmo envelope.
#   2. Captura completa de metadados de status (recipient_id, message_id,
#      timestamp, estado da entrega). Essencial para atualização do painel
#      do atendente (ícones de enviado/entregue/lido/falha).
#   3. Extração de informações de mídia (media_id, mime_type, filename)
#      para mensagens de imagem, áudio, vídeo, documento e sticker.
#   4. Suporte a mensagens de localização, contatos e reactions.
#   5. Lógica defensiva mantida: eventos de status NUNCA geram respostas
#      automáticas, eliminando o risco de loop infinito.
# ==============================================================================
from __future__ import annotations

import logging
from dataclasses import dataclass, field
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass
    StrEnum = Enum
except ImportError:
    from enum import Enum
    StrEnum = Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerações
# ---------------------------------------------------------------------------

class WebhookEventType(StrEnum):
    """Tipos de evento reconhecidos pelo parser."""

    MESSAGE = "message"
    STATUS = "status"
    IGNORED = "ignored"


class MessageCategory(StrEnum):
    """Categorias de mensagem suportadas pela Meta Cloud API."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    BUTTON = "button"
    INTERACTIVE = "interactive"
    REACTION = "reaction"
    UNKNOWN = "unknown"


class DeliveryStatus(StrEnum):
    """Estados de entrega reportados pela Meta."""

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Estrutura de dados
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ParsedWebhookEvent:
    """
    Resultado normalizado do parsing de um evento individual do webhook.

    Campos condicionais:
      - Campos de mensagem (chat_id, text, media_*) são preenchidos
        quando type == MESSAGE.
      - Campos de status (status_value, status_message_id, status_recipient_id)
        são preenchidos quando type == STATUS.
    """

    type: WebhookEventType
    chat_id: str | None = None
    text: str | None = None
    message_category: MessageCategory = MessageCategory.UNKNOWN
    media_id: str | None = None
    media_mime_type: str | None = None
    media_filename: str | None = None
    media_caption: str | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None
    status_value: DeliveryStatus | None = None
    status_message_id: str | None = None
    status_recipient_id: str | None = None
    timestamp: str | None = None
    raw_change: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def parse_incoming_webhook(
    payload: dict[str, Any],
) -> list[ParsedWebhookEvent]:
    """
    Interpreta o envelope JSON completo da Meta Cloud API e retorna uma lista
    de eventos normalizados.

    Regras de processamento:
      1. Varre TODOS os ``entry`` → ``changes`` do envelope.
      2. Para cada *change*, extrai independentemente as mensagens e os
         eventos de status, gerando um ``ParsedWebhookEvent`` por item.
      3. Eventos de status são classificados como ``WebhookEventType.STATUS``
         e **nunca** como ``MESSAGE``, garantindo que o motor de respostas
         do bot não os processe (eliminação do loop infinito).
      4. Se o envelope não contiver nenhum evento reconhecível, retorna uma
         lista com um único evento ``IGNORED``.

    Returns:
        Lista de eventos parseados. Lista vazia apenas se ``payload`` for
        inválido (não-dict ou sem ``entry``).
    """
    if not isinstance(payload, dict):
        logger.warning("Webhook recebido não é um dict: %r", type(payload))
        return [_ignored_event(payload)]

    entries = payload.get("entry") or []
    if not entries:
        logger.debug("Webhook sem 'entry' — ignorando.")
        return [_ignored_event(payload)]

    events: list[ParsedWebhookEvent] = []

    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value")
            if not isinstance(value, dict):
                continue

            events.extend(_parse_messages(value, change))
            events.extend(_parse_statuses(value, change))

    if not events:
        logger.debug("Webhook sem eventos reconhecíveis.")
        return [_ignored_event(payload)]

    logger.info(
        "Webhook parseado: %d mensagem(ns), %d status, %d ignorado(s).",
        sum(1 for e in events if e.type == WebhookEventType.MESSAGE),
        sum(1 for e in events if e.type == WebhookEventType.STATUS),
        sum(1 for e in events if e.type == WebhookEventType.IGNORED),
    )
    return events


# ---------------------------------------------------------------------------
# Parsers internos
# ---------------------------------------------------------------------------

def _parse_messages(
    value: dict[str, Any],
    change: dict[str, Any],
) -> list[ParsedWebhookEvent]:
    """Extrai todos os eventos de mensagem de um bloco ``value``."""
    messages = value.get("messages") or []
    results: list[ParsedWebhookEvent] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        chat_id = msg.get("from")
        if not chat_id:
            logger.debug("Mensagem sem campo 'from' — descartada.")
            continue

        category = _detect_message_category(msg)
        text = _extract_text(msg, category)
        media = _extract_media_info(msg, category)

        results.append(
            ParsedWebhookEvent(
                type=WebhookEventType.MESSAGE,
                chat_id=chat_id,
                text=text,
                message_category=category,
                media_id=media.get("id"),
                media_mime_type=media.get("mime_type"),
                media_filename=media.get("filename"),
                media_caption=media.get("caption"),
                location_latitude=media.get("latitude"),
                location_longitude=media.get("longitude"),
                timestamp=msg.get("timestamp"),
                raw_change=change,
            )
        )

    return results


def _parse_statuses(
    value: dict[str, Any],
    change: dict[str, Any],
) -> list[ParsedWebhookEvent]:
    """Extrai todos os eventos de status (DLR) de um bloco ``value``."""
    statuses = value.get("statuses") or []
    results: list[ParsedWebhookEvent] = []

    for st in statuses:
        if not isinstance(st, dict):
            continue

        raw_status = st.get("status", "")
        try:
            delivery = DeliveryStatus(raw_status)
        except ValueError:
            logger.debug("Status desconhecido '%s' — tratado como IGNORED.", raw_status)
            delivery = None

        results.append(
            ParsedWebhookEvent(
                type=WebhookEventType.STATUS if delivery else WebhookEventType.IGNORED,
                status_value=delivery,
                status_message_id=st.get("id"),
                status_recipient_id=st.get("recipient_id"),
                timestamp=st.get("timestamp"),
                raw_change=change,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Detectores e extratores
# ---------------------------------------------------------------------------

def _detect_message_category(msg: dict[str, Any]) -> MessageCategory:
    """Determina a categoria da mensagem com base nos campos presentes."""
    if "text" in msg:
        return MessageCategory.TEXT
    if "button" in msg:
        return MessageCategory.BUTTON
    if "interactive" in msg:
        return MessageCategory.INTERACTIVE
    if "location" in msg:
        return MessageCategory.LOCATION
    if "contacts" in msg:
        return MessageCategory.CONTACTS
    if "reaction" in msg:
        return MessageCategory.REACTION
    for media_type in (
        MessageCategory.IMAGE,
        MessageCategory.AUDIO,
        MessageCategory.VIDEO,
        MessageCategory.DOCUMENT,
        MessageCategory.STICKER,
    ):
        if media_type.value in msg:
            return media_type
    return MessageCategory.UNKNOWN


def _extract_text(
    msg: dict[str, Any],
    category: MessageCategory,
) -> str | None:
    """
    Extrai o conteúdo textual da mensagem conforme sua categoria.

    Para mídias, retorna a legenda (``caption``) quando disponível.
    """
    match category:
        case MessageCategory.TEXT:
            text_block = msg.get("text")
            return text_block.get("body") if isinstance(text_block, dict) else None

        case MessageCategory.BUTTON:
            button_block = msg.get("button")
            return button_block.get("text") if isinstance(button_block, dict) else None

        case MessageCategory.INTERACTIVE:
            interactive = msg.get("interactive", {})
            if isinstance(interactive.get("button_reply"), dict):
                return interactive["button_reply"].get("title")
            if isinstance(interactive.get("list_reply"), dict):
                return interactive["list_reply"].get("title")
            return None

        case MessageCategory.LOCATION:
            loc = msg.get("location", {})
            name = loc.get("name", "")
            address = loc.get("address", "")
            parts = [p for p in (name, address) if p]
            return " | ".join(parts) if parts else "Localização compartilhada"

        case MessageCategory.REACTION:
            reaction = msg.get("reaction", {})
            emoji = reaction.get("emoji", "")
            return f"Reação: {emoji}" if emoji else None

        case (
            MessageCategory.IMAGE
            | MessageCategory.VIDEO
            | MessageCategory.DOCUMENT
        ):
            media_block = msg.get(category.value, {})
            return media_block.get("caption") if isinstance(media_block, dict) else None

        case _:
            return None


def _extract_media_info(
    msg: dict[str, Any],
    category: MessageCategory,
) -> dict[str, Any]:
    """
    Extrai metadados de mídia (ID, MIME, filename, coordenadas).

    Retorna um dicionário vazio para categorias que não possuem mídia.
    """
    info: dict[str, Any] = {}

    if category in (
        MessageCategory.IMAGE,
        MessageCategory.AUDIO,
        MessageCategory.VIDEO,
        MessageCategory.DOCUMENT,
        MessageCategory.STICKER,
    ):
        media_block = msg.get(category.value, {})
        if isinstance(media_block, dict):
            info["id"] = media_block.get("id")
            info["mime_type"] = media_block.get("mime_type")
            info["filename"] = media_block.get("filename")
            info["caption"] = media_block.get("caption")

    elif category == MessageCategory.LOCATION:
        loc = msg.get("location", {})
        if isinstance(loc, dict):
            info["latitude"] = loc.get("latitude")
            info["longitude"] = loc.get("longitude")

    return info


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _ignored_event(raw: Any) -> ParsedWebhookEvent:
    """Constrói um evento do tipo IGNORED."""
    return ParsedWebhookEvent(
        type=WebhookEventType.IGNORED,
        raw_change=raw if isinstance(raw, dict) else {},
    )


__all__ = [
    "DeliveryStatus",
    "MessageCategory",
    "ParsedWebhookEvent",
    "WebhookEventType",
    "parse_incoming_webhook",
]