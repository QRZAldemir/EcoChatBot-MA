# app/adapters/providers/telegram_adapter.py
"""
Módulo: telegram_adapter.py

Explicação:
Adaptador para Telegram Bot API.
Implementa BaseMessageAdapter para abstração do provedor Telegram.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from app.adapters.base_message_adapter import BaseMessageAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(BaseMessageAdapter):
    """
    Adaptador para Telegram Bot API.
    """

    def __init__(self, bot_token: Optional[str] = None):
        self._bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._base_url = f"https://api.telegram.org/bot{self._bot_token}"
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    async def send_text(
        self,
        chat_id: str,
        text: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mensagem de texto via Telegram Bot API."""
        url = f"{self._base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, **kwargs}

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"TelegramAdapter.send_text | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("TelegramAdapter.send_text | Timeout")
            raise

    async def send_media(
        self,
        chat_id: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Envia mídia via Telegram Bot API."""
        if media_type == "image":
            method = "sendPhoto"
            media_key = "photo"
        elif media_type == "video":
            method = "sendVideo"
            media_key = "video"
        elif media_type == "audio":
            method = "sendAudio"
            media_key = "audio"
        else:
            method = "sendDocument"
            media_key = "document"

        url = f"{self._base_url}/{method}"
        payload = {"chat_id": chat_id, media_key: media_url, **kwargs}
        if caption:
            payload["caption"] = caption

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"TelegramAdapter.send_media | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("TelegramAdapter.send_media | Timeout")
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
        """Envia menu inline via Telegram (usando inline keyboard)."""
        # Telegram não tem sendList idêntico - usa InlineKeyboardMarkup
        url = f"{self._base_url}/sendMessage"
        text = f"{title}\n\n{description}"
        if footer:
            text += f"\n\n{footer}"

        # Converte sections para inline keyboard (simplificado)
        keyboard = []
        for section in sections:
            for row in section.get("rows", []):
                keyboard.append([{"text": row.get("title", ""), "callback_data": row.get("rowId", "")}])

        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {"inline_keyboard": keyboard},
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"TelegramAdapter.send_list | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("TelegramAdapter.send_list | Timeout")
            raise

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Padroniza webhook do Telegram."""
        try:
            message = payload.get("message", payload.get("callback_query", {}).get("message", {}))
            callback_data = payload.get("callback_query", {}).get("data", "")

            sender = str(message.get("from", {}).get("id", ""))
            chat_id = str(message.get("chat", {}).get("id", sender))

            text = message.get("text", "") or callback_data
            msg_type = "text" if text else "media"

            if callback_data:
                msg_type = "interactive"

            return {
                "sender": sender,
                "chat_id": chat_id,
                "text": text,
                "type": msg_type,
                "raw": payload,
            }
        except Exception as e:
            logger.error(f"TelegramAdapter.parse_webhook | Erro: {e}")
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
