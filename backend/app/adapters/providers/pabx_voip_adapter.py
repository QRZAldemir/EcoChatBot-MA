# app/adapters/providers/pabx_voip_adapter.py
"""
Módulo: pabx_voip_adapter.py

Explicação:
Adaptador para PABX/VoIP (MicroSIP, Asterisk, FreePBX, etc.).
Implementa BaseMessageAdapter para integrar sistemas de telefonia IP.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from app.adapters.base_message_adapter import BaseMessageAdapter

logger = logging.getLogger(__name__)


class PABXVoIPAdapter(BaseMessageAdapter):
    """
    Adaptador para PABX/VoIP.

    Responsabilidade: Abstrair integrações com sistemas de telefonia IP
    como MicroSIP, Asterisk, FreePBX, 3CX, etc.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_type: str = "bearer",
    ):
        self._base_url = base_url or os.getenv("PABX_API_URL", "")
        self._api_key = api_key or os.getenv("PABX_API_KEY", "")
        self._auth_type = auth_type
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._auth_type == "apikey":
            headers["X-API-Key"] = self._api_key
        return headers

    async def send_text(
        self,
        chat_id: str,
        text: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Envia mensagem/texto via PABX/VoIP.
        Pode ser usado para envio de SMS via tronco VoIP ou notificações.
        """
        url = f"{self._base_url}/messages/send"
        payload = {
            "to": chat_id,
            "text": text,
            "channel": "sms",
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PABXVoIPAdapter.send_text | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("PABXVoIPAdapter.send_text | Timeout")
            raise

    async def send_media(
        self,
        chat_id: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Envia mídia via PABX/VoIP.
        Dependendo do provedor, pode não ser suportado - retorna erro controlado.
        """
        url = f"{self._base_url}/messages/send"
        payload = {
            "to": chat_id,
            "media": media_url,
            "media_type": media_type,
            "caption": caption,
            "channel": "mms",
            **kwargs
        }

        try:
            response = await self._client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PABXVoIPAdapter.send_media | HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error("PABXVoIPAdapter.send_media | Timeout")
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
        """
        Envia menu/lista via PABX/VoIP.
        Para sistemas VoIP tradicionais, pode enviar como texto formatado.
        """
        # Formata como texto para PABX/SMS
        lines = [title, description, ""]
        for section in sections:
            lines.append(f"--- {section.get(title, )} ---")
            for row in section.get("rows", []):
                lines.append(f"{row.get(rowId, )}: {row.get(title, )}")
                if row.get("description"):
                    lines.append(f"  {row.get(description)}")
        if footer:
            lines.append("")
            lines.append(footer)

        return await self.send_text(chat_id, "\n".join(lines), **kwargs)

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Padroniza webhook de PABX/VoIP."""
        try:
            sender = payload.get("from", payload.get("caller", ""))
            chat_id = sender
            text = payload.get("text", payload.get("body", payload.get("content", "")))
            msg_type = payload.get("type", "text")

            return {
                "sender": sender,
                "chat_id": chat_id,
                "text": text,
                "type": msg_type,
                "raw": payload,
            }
        except Exception as e:
            logger.error(f"PABXVoIPAdapter.parse_webhook | Erro: {e}")
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
