# app/adapters/providers/meta_cloud_adapter.py
"""
Módulo: meta_cloud_adapter.py

Explicação:
Adaptador para Meta Cloud API (WhatsApp Business Cloud).
Implementa BaseMessageAdapter isolando a API do Meta da camada de negócio,
permitindo polimorfismo com os demais provedores.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from app.adapters.base_message_adapter import BaseMessageAdapter

logger = logging.getLogger(__name__)


class MetaCloudAdapter(BaseMessageAdapter):
    """
    Adaptador para Meta Cloud API (WhatsApp Business Cloud API).

    Responsabilidade única: abstrair as chamadas da Graph API do WhatsApp
    Business para o contrato definido em BaseMessageAdapter.
    """

    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://graph.facebook.com/v19.0",
    ):
        self._phone_number_id = phone_number_id or os.getenv("META_PHONE_NUMBER_ID", "")
        self._access_token = access_token or os.getenv("META_ACCESS_TOKEN", "")
        self._base_url = base_url
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def send_text(
        self,
        chat_id: str,
        text: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mensagem de texto via Meta Cloud API."""
        url = f"{self._base_url}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": chat_id,
            "type": "text",
            "text": {"body": text},
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "MetaCloudAdapter.send_text | HTTP %s | %s",
                e.response.status_code,
                e.response.text[:200],
            )
            raise
        except httpx.TimeoutException:
            logger.error("MetaCloudAdapter.send_text | timeout")
            raise

    async def send_media(
        self,
        chat_id: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mídia via Meta Cloud API."""
        url = f"{self._base_url}/{self._phone_number_id}/messages"

        media_obj: Dict[str, Any] = {"link": media_url}
        if caption and media_type in ("image", "video", "document"):
            media_obj["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": chat_id,
            "type": media_type,
            media_type: media_obj,
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "MetaCloudAdapter.send_media | HTTP %s | %s",
                e.response.status_code,
                e.response.text[:200],
            )
            raise
        except httpx.TimeoutException:
            logger.error("MetaCloudAdapter.send_media | timeout")
            raise

    async def send_list(
        self,
        chat_id: str,
        title: str,
        description: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        footer: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia lista interativa via Meta Cloud API."""
        url = f"{self._base_url}/{self._phone_number_id}/messages"

        interactive: Dict[str, Any] = {
            "type": "list",
            "header": {"type": "text", "text": title},
            "body": {"text": description},
            "action": {
                "button": button_text,
                "sections": sections,
            },
        }
        if footer:
            interactive["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": chat_id,
            "type": "interactive",
            "interactive": interactive,
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "MetaCloudAdapter.send_list | HTTP %s | %s",
                e.response.status_code,
                e.response.text[:200],
            )
            raise
        except httpx.TimeoutException:
            logger.error("MetaCloudAdapter.send_list | timeout")
            raise

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Padroniza webhook da Meta Cloud API."""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return {
                    "sender": "",
                    "chat_id": "",
                    "text": "",
                    "type": "status",
                    "raw": payload,
                }

            msg = messages[0]
            sender = msg.get("from", "")
            msg_type = msg.get("type", "text")
            text = ""

            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                interactive = msg.get("interactive", {})
                if interactive.get("type") == "list_reply":
                    text = interactive["list_reply"].get("id", "")
                elif interactive.get("type") == "button_reply":
                    text = interactive["button_reply"].get("id", "")

            return {
                "sender": sender,
                "chat_id": sender,
                "text": text,
                "type": msg_type,
                "raw": payload,
            }
        except Exception as e:
            logger.error("MetaCloudAdapter.parse_webhook | erro: %s", e)
            return {
                "sender": "",
                "chat_id": "",
                "text": "",
                "type": "unknown",
                "raw": payload,
            }

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "MetaCloudAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()