# ==============================================================================
# ARQUIVO.....: facebook_webhook_parser.py
# PROJETO.....: EcoChatBot-MA
# MÓDULO......: Parser de Webhook Facebook Messenger
# VERSÃO......: 1.0.0
# AUTOR.......: Aldemir Queiroz da Silva
# DATA........: 10/10/2026
# ==============================================================================
# DESCRIÇÃO...:
# Parser do webhook unificado da Meta para Facebook Messenger.
#
# CORREÇÕES APLICADAS:
#   1. Filtragem de ``object == "page"``: rejeita eventos de Instagram e
#      outros objetos que compartilham o mesmo endpoint de webhook.
#   2. Descarte de mensagens de eco (``is_echo: True``): impede que o bot
#      processe respostas do atendente humano como mensagens do cliente.
#   3. Suporte a eventos de ``postback`` (botões de Get Started, menus).
#   4. Suporte a ``optin`` (plugin de login) e ``referral``.
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
from typing import Any

logger = logging.getLogger(__name__)


class MessengerEventType(StrEnum):
    MESSAGE = "message"
    POSTBACK = "postback"
    OPTIN = "optin"
    REFERRAL = "referral"
    IGNORED = "ignored"


@dataclass(slots=True)
class MessengerEvent:
    """Evento normalizado do Facebook Messenger."""

    type: MessengerEventType
    sender_id: str | None = None
    recipient_id: str | None = None
    text: str | None = None
    postback_payload: str | None = None
    referral_ref: str | None = None
    timestamp: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_messenger_webhook(
    payload: dict[str, Any],
) -> list[MessengerEvent]:
    """
    Interpreta o envelope JSON do webhook do Facebook Messenger.

    Regras de admissão:
      1. ``payload["object"]`` DEVE ser ``"page"``. Qualquer outro valor
         (ex.: ``"instagram"``) resulta em lista vazia.
      2. Mensagens com ``message.is_echo == True`` são descartadas
         silenciosamente — representam respostas do atendente humano.
      3. Cada evento ``messaging`` é classificado independentemente.

    Returns:
        Lista de eventos normalizados. Lista vazia se o payload for
        rejeitado ou não contiver eventos reconhecíveis.
    """
    if not isinstance(payload, dict):
        logger.warning("Payload inválido (não-dict): %r", type(payload))
        return []

    # ── Regra 1: Filtragem de objeto ──────────────────────────────────
    if payload.get("object") != "page":
        logger.debug(
            "Webhook rejeitado: object='%s' (esperado 'page').",
            payload.get("object"),
        )
        return []

    events: list[MessengerEvent] = []

    for entry in payload.get("entry", []):
        for messaging in entry.get("messaging", []):
            event = _classify_messaging_event(messaging)
            if event is not None:
                events.append(event)

    logger.info("Messenger webhook: %d evento(s) parseado(s).", len(events))
    return events


# ---------------------------------------------------------------------------
# Classificador interno
# ---------------------------------------------------------------------------

def _classify_messaging_event(
    messaging: dict[str, Any],
) -> MessengerEvent | None:
    """Classifica um bloco ``messaging`` individual."""
    sender = messaging.get("sender", {}).get("id")
    recipient = messaging.get("recipient", {}).get("id")
    timestamp = messaging.get("timestamp")

    # ── Regra 2: Descarte de eco ──────────────────────────────────────
    message_block = messaging.get("message", {})
    if isinstance(message_block, dict) and message_block.get("is_echo") is True:
        logger.debug("Mensagem de eco descartada (sender=%s).", sender)
        return None

    # ── Mensagem de texto ou attachment ───────────────────────────────
    if message_block:
        text = message_block.get("text")
        # Se não há texto, pode ser um attachment (imagem, áudio, etc.)
        if not text and "attachments" in message_block:
            attachments = message_block["attachments"]
            if attachments:
                text = f"[{attachments[0].get('type', 'attachment')}]"
        return MessengerEvent(
            type=MessengerEventType.MESSAGE,
            sender_id=sender,
            recipient_id=recipient,
            text=text,
            timestamp=timestamp,
            raw=messaging,
        )

    # ── Postback (botões, Get Started) ────────────────────────────────
    postback = messaging.get("postback")
    if isinstance(postback, dict):
        return MessengerEvent(
            type=MessengerEventType.POSTBACK,
            sender_id=sender,
            recipient_id=recipient,
            text=postback.get("title"),
            postback_payload=postback.get("payload"),
            timestamp=timestamp,
            raw=messaging,
        )

    # ── Opt-in (plugin de login / checkbox) ───────────────────────────
    optin = messaging.get("optin")
    if isinstance(optin, dict):
        return MessengerEvent(
            type=MessengerEventType.OPTIN,
            sender_id=sender,
            recipient_id=recipient,
            text=optin.get("ref"),
            timestamp=timestamp,
            raw=messaging,
        )

    # ── Referral ──────────────────────────────────────────────────────
    referral = messaging.get("referral")
    if isinstance(referral, dict):
        return MessengerEvent(
            type=MessengerEventType.REFERRAL,
            sender_id=sender,
            recipient_id=recipient,
            referral_ref=referral.get("ref"),
            timestamp=timestamp,
            raw=messaging,
        )

    logger.debug("Evento 'messaging' não classificado: %s", messaging.keys())
    return None


__all__ = [
    "MessengerEvent",
    "MessengerEventType",
    "parse_messenger_webhook",
]