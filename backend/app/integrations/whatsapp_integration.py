# ==============================================================================
# ARQUIVO.....: meta_cloud_webhook_parser.py
# AUTOR.......: (refatoração para estudo)
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Parser de Webhook Meta Cloud API (Graph API)
# VERSÃO......: 2.0.0 (Correção de loop infinito com eventos 'statuses')
# LINGUAGEM...: Python 3.12+
# ==============================================================================
# DESCRIÇÃO...:
# Parser responsável por interpretar o envelope JSON enviado pela Meta Cloud API
# no endpoint de webhook do WhatsApp Business.
#
# PROBLEMA CORRIGIDO (bug de loop infinito):
#   A Meta envia, no MESMO envelope, dois tipos de evento dentro de
#   entry[].changes[].value:
#     (a) "messages"   -> mensagens enviadas por clientes (devem ser processadas)
#     (b) "statuses"   -> notificações de entrega/leitura (NÃO são mensagens)
#
#   Se o parser tratar um evento de "statuses" como se fosse uma mensagem
#   recebida, o bot responde à própria notificação de entrega, a Meta gera
#   novo status, o bot responde de novo... => LOOP INFINITO DE AUTO-RESPOSTAS.
#
# CORREÇÃO:
#   O parser DEVE:
#     1. Verificar explicitamente a presença de "statuses".
#     2. Se houver "statuses" e NÃO houver "messages", retornar type="status".
#     3. Só processar como mensagem quando existir "messages".
# ==============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Tipo canônico do resultado do parsing.
# Usamos Literal para deixar explícito no tipo quais valores são válidos.
ParsedEventType = Literal["message", "status", "ignored"]


@dataclass(slots=True)
class ParsedWebhookEvent:
    """
    Resultado normalizado do parsing de um webhook da Meta Cloud API.

    Atributos:
        type:     "message" -> deve ser processado pelo BotService
                  "status"  -> notificação de entrega/leitura (ignorar)
                  "ignored" -> evento desconhecido ou irrelevante
        chat_id:  número do cliente (só faz sentido quando type == "message")
        text:     conteúdo textual da mensagem (quando aplicável)
        raw:      payload original, útil para auditoria e debugging
    """

    type: ParsedEventType
    chat_id: str | None = None
    text: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_incoming_webhook(payload: dict[str, Any]) -> ParsedWebhookEvent:
    """
    Interpreta o envelope JSON recebido da Meta Cloud API.

    Estrutura típica (simplificada) do payload da Meta:
        {
          "object": "whatsapp_business_account",
          "entry": [
            {
              "id": "...",
              "changes": [
                {
                  "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {...},
                    # OU "messages" (cliente enviou) OU "statuses" (entrega/leitura)
                    "messages": [...],
                    "statuses": [...]
                  },
                  "field": "messages"
                }
              ]
            }
          ]
        }

    REGRA DE OURO (correção do loop infinito):
        Se o value contiver "statuses" e NÃO contiver "messages",
        retornamos type="status" e NÃO processamos como mensagem.
    """
    # ----------------------------------------------------------------
    # 1. Validação básica do envelope
    # ----------------------------------------------------------------
    if not isinstance(payload, dict):
        logger.warning("Webhook recebido não é um dict: %r", type(payload))
        return ParsedWebhookEvent(type="ignored", raw=payload or {})

    entries = payload.get("entry") or []
    if not entries:
        logger.debug("Webhook sem 'entry' — ignorando.")
        return ParsedWebhookEvent(type="ignored", raw=payload)

    # ----------------------------------------------------------------
    # 2. Percorrer entries -> changes -> value
    #    (a Meta pode agrupar vários eventos no mesmo POST)
    # ----------------------------------------------------------------
    for entry in entries:
        for change in (entry.get("changes") or []):
            value = change.get("value") or {}

            # --------------------------------------------------------
            # 3. CORREÇÃO DO BUG: detectar 'statuses' ANTES de 'messages'
            # --------------------------------------------------------
            # A Meta envia "statuses" para notificar entrega/leitura.
            # Esses eventos NÃO são mensagens de clientes.
            # Se tratarmos como mensagem, o bot responde à própria
            # notificação e entra em loop infinito.
            #
            # Regra:
            #   - Se existir "statuses" e NÃO existir "messages" -> status
            #   - Se existir "messages" -> mensagem (mesmo que também
            #     exista "statuses" no mesmo value, priorizamos messages)
            # --------------------------------------------------------
            has_statuses = "statuses" in value and value.get("statuses")
            has_messages = "messages" in value and value.get("messages")

            if has_statuses and not has_messages:
                logger.debug(
                    "Webhook de status recebido (entrega/leitura). "
                    "Ignorando para evitar loop infinito."
                )
                return ParsedWebhookEvent(type="status", raw=payload)

            # --------------------------------------------------------
            # 4. Processar mensagem real do cliente
            # --------------------------------------------------------
            if has_messages:
                first_msg = value["messages"][0]
                chat_id = first_msg.get("from")  # número do cliente
                text = _extract_text(first_msg)

                if not chat_id:
                    logger.warning("Mensagem sem 'from' — ignorando.")
                    return ParsedWebhookEvent(type="ignored", raw=payload)

                return ParsedWebhookEvent(
                    type="message",
                    chat_id=chat_id,
                    text=text,
                    raw=payload,
                )

    # ----------------------------------------------------------------
    # 5. Nenhum evento reconhecido
    # ----------------------------------------------------------------
    logger.debug("Webhook sem 'messages' nem 'statuses' reconhecíveis.")
    return ParsedWebhookEvent(type="ignored", raw=payload)


def _extract_text(message: dict[str, Any]) -> str | None:
    """
    Extrai o texto de uma mensagem da Meta Cloud API.

    A Meta usa estruturas diferentes conforme o tipo:
      - text:     {"text": {"body": "..."}}
      - button:   {"button": {"text": "..."}}
      - interactive: {"interactive": {"button_reply": {"title": "..."}}}
    """
    if "text" in message:
        return message["text"].get("body")

    if "button" in message:
        return message["button"].get("text")

    if "interactive" in message:
        interactive = message["interactive"]
        # Resposta de botão
        if "button_reply" in interactive:
            return interactive["button_reply"].get("title")
        # Resposta de lista
        if "list_reply" in interactive:
            return interactive["list_reply"].get("title")

    # Outros tipos (áudio, imagem, etc.) não têm texto puro
    return None


__all__ = ["ParsedWebhookEvent", "parse_incoming_webhook"]