# app/adapters/providers/evolution_adapter.py
"""
Módulo: evolution_adapter.py

Explicação:
Adaptador para Evolution API (WhatsApp). Implementa BaseMessageAdapter
proporcionando abstração entre a camada de negócio e a Evolution API,
seguindo princípios de POO (polimorfismo, encapsulamento e abstração).
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from app.adapters.base_message_adapter import BaseMessageAdapter

logger = logging.getLogger(__name__)


class EvolutionAdapter(BaseMessageAdapter):
    """
    Adaptador para Evolution API.

    Responsabilidade: Traduz chamadas genéricas do BaseMessageAdapter
    para chamadas específicas da Evolution API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_header: str = "apikey",
    ):
        self._base_url = base_url or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        self._api_key = api_key or os.getenv("EVOLUTION_API_KEY", "")
        self._auth_header = auth_header or os.getenv("EVOLUTION_AUTH_HEADER", "apikey")
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        return {
            self._auth_header: self._api_key,
            "Content-Type": "application/json",
        }

    async def send_text(
        self,
        chat_id: str,
        text: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mensagem de texto via Evolution API."""
        instance = kwargs.pop("instance", kwargs.pop("instance_name", ""))
        if not instance:
            raise ValueError("Parâmetro instance é obrigatório")

        url = f"{self._base_url}/message/sendText/{instance}"
        payload = {"number": chat_id, "text": text, "delay": kwargs.pop("delay", 1200), **kwargs}

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"EvolutionAdapter.send_text | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("EvolutionAdapter.send_text | Timeout")
            raise

    async def send_media(
        self,
        chat_id: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mídia via Evolution API."""
        instance = kwargs.pop("instance", kwargs.pop("instance_name", ""))
        if not instance:
            raise ValueError("Parâmetro instance é obrigatório")

        url = f"{self._base_url}/message/sendMedia/{instance}"
        payload = {
            "number": chat_id,
            "mediatype": media_type,
            "media": media_url,
            **kwargs
        }
        if caption:
            payload["caption"] = caption

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"EvolutionAdapter.send_media | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("EvolutionAdapter.send_media | Timeout")
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
        """Envia lista interativa via Evolution API."""
        instance = kwargs.pop("instance", kwargs.pop("instance_name", ""))
        if not instance:
            raise ValueError("Parâmetro instance é obrigatório")

        url = f"{self._base_url}/message/sendList/{instance}"
        payload = {
            "number": chat_id,
            "title": title,
            "description": description,
            "buttonText": button_text,
            "sections": sections,
            "footerText": footer or "",
            "delay": kwargs.pop("delay", 1200),
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"EvolutionAdapter.send_list | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("EvolutionAdapter.send_list | Timeout")
            raise

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Padroniza webhook da Evolution API."""
        try:
            data = payload.get("data", payload)
            key = data.get("key", {})
            message = data.get("message", {})

            sender = key.get("remoteJid", "").replace("@s.whatsapp.net", "").replace("@g.us", "")
            chat_id = sender

            text = ""
            msg_type = "text"

            if message.get("conversation"):
                text = message["conversation"]
                msg_type = "text"
            elif message.get("extendedTextMessage", {}).get("text"):
                text = message["extendedTextMessage"]["text"]
                msg_type = "text"
            elif message.get("imageMessage"):
                msg_type = "image"
            elif message.get("videoMessage"):
                msg_type = "video"
            elif message.get("audioMessage"):
                msg_type = "audio"
            elif message.get("documentMessage"):
                msg_type = "document"
            elif message.get("listResponseMessage"):
                text = message["listResponseMessage"].get("singleSelectReply", {}).get("selectedRowId", "")
                msg_type = "list_response"

            return {
                "sender": sender,
                "chat_id": chat_id,
                "text": text,
                "type": msg_type,
                "raw": payload,
            }
        except Exception as e:
            logger.error(f"EvolutionAdapter.parse_webhook | Erro: {e}")
            return {
                "sender": "",
                "chat_id": "",
                "text": "",
                "type": "unknown",
                "raw": payload,
            }

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
