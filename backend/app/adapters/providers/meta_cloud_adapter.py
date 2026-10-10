# app/adapters/providers/meta_cloud_adapter.py
"""
Módulo: meta_cloud_adapter.py

EXPANÇÃO DA ESTRUTURA DE ADAPTERS:
├── base_message_adapter.py  (BaseMessageAdapter - ABC)
│   ├── define contrato: send_text, send_media, send_list, parse_webhook
│   └── estabelece polimorfismo entre provedores
└── providers/
    ├── evolution_adapter.py   (herda BaseMessageAdapter)
    ├── meta_cloud_adapter.py  (herda BaseMessageAdapter) ← ATUAL
    ├── telegram_adapter.py    (herda BaseMessageAdapter)
    └── pabx_voip_adapter.py   (herda BaseMessageAdapter)

FUNCIONALIDADE:
Adaptador concreto para Meta Cloud API (WhatsApp Business Cloud - Graph API v19.0).
Responsável por normalizar envio de mensagens (texto, mídia, listas) e parsing
de webhooks provenientes da Meta Cloud API.

HERANÇA:
Herda de BaseMessageAdapter (ABC) - implementa obrigatoriamente:
- send_text(self, chat_id, text, **kwargs)
- send_media(self, chat_id, media_url, media_type, caption, **kwargs)
- send_list(self, chat_id, title, description, button_text, sections, footer, **kwargs)
- parse_webhook(self, payload)

PADRÃO ARQUITETURAL:
Adapter Pattern - isola integração direta com Graph API, evitando acoplamento
entre camada de negócio (bot_service) e provedor específico (Meta). Permite
intercambialidade via AdapterFactory.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from app.adapters.base_message_adapter import BaseMessageAdapter

logger = logging.getLogger(__name__)


class MetaCloudAdapter(BaseMessageAdapter):
    """
    Adaptador Meta Cloud API (WhatsApp Business Cloud).

    HERANÇA: MetaCloudAdapter(BaseMessageAdapter)
    Implementa contrato definido em BaseMessageAdapter.

    ATRIBUTOS:
    - _phone_number_id (str): ID do número WhatsApp Business (META_PHONE_NUMBER_ID)
    - _access_token (str): Token de acesso permanente (META_ACCESS_TOKEN)
    - _base_url (str): Base Graph API (default https://graph.facebook.com/v19.0)
    - _client (httpx.AsyncClient): Cliente HTTP assíncrono (timeout 30s)

    COMPORTAMENTO:
    - send_text: POST /{phone_number_id}/messages com type=text
    - send_media: POST /{phone_number_id}/messages com type=<media_type>
                 • image/video/document: usa {"link": media_url}; caption apenas image/video
                 • audio: faz upload prévio para /{phone_number_id}/media → {"id": media_id}
    - send_list: POST /{phone_number_id}/messages com type=interactive (list)
    - parse_webhook: extrai sender/chat_id/text a partir do envelope Meta Cloud
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

        # ------------------------------------------------------------------
        # REGRAS DA GRAPH API (WhatsApp Business Cloud):
        #   1. "caption" é aceito APENAS para image e video. Enviar caption
        #      em document/audio retorna HTTP 400.
        #   2. Áudio NÃO pode ser enviado por URL pública
        #      ("audio": {"link": ...}). A Meta exige upload prévio em
        #      POST /{phone_number_id}/media para gerar um media_id e só
        #      então enviar ("audio": {"id": media_id}).
        # ------------------------------------------------------------------
        if media_type == "audio":
            media_id = await self._upload_media(media_url)
            media_obj: Dict[str, Any] = {"id": media_id}
        else:
            media_obj = {"link": media_url}
            if caption and media_type in ("image", "video"):
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

    async def _upload_media(self, media_url: str) -> str:
        """
        Upload prévio para Meta Cloud API.

        ROTINA INTERNA (privada): chamada exclusivamente em send_media quando
        media_type == 'audio'.

        FLUXO OBRIGATÓRIO (Graph API):
        1. GET media_url → baixa arquivo (Content-Type + bytes)
        2. POST /{phone_number_id}/media (multipart/form-data, campo 'file')
           - headers: Authorization: Bearer <access_token> (sem Content-Type fixo)
        3. Retorna {"id": "<media_id>"}
        4. Usar {"audio": {"id": <media_id>}} em /{phone_number_id}/messages

        MOTIVO DA NECESSIDADE:
        A Meta Cloud API NÃO aceita envio de áudio via URL pública direta
        ("audio": {"link": "..."}). É obrigatório gerar media_id via upload
        prévio. Documentação Meta: "Upload media" + "Send audio using media ID".

        PARÂMETROS:
        - media_url (str): URL pública do arquivo de áudio (fornecida pelo app)

        RETORNO:
        - str: media_id gerado pela Graph API

        EXCEÇÕES:
        - httpx.HTTPStatusError: falha no download/upload
        - RuntimeError: resposta sem campo 'id'
        """
        upload_url = f"{self._base_url}/{self._phone_number_id}/media"
        # Sem Content-Type fixo: o httpx define o boundary multipart/form-data.
        upload_headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        download = await self._client.get(media_url)
        download.raise_for_status()

        file_name = media_url.rstrip("/").rsplit("/", 1)[-1] or "audio"
        content_type = download.headers.get("content-type") or "application/octet-stream"

        response = await self._client.post(
            upload_url,
            headers=upload_headers,
            files={"file": (file_name, download.content, content_type)},
        )
        response.raise_for_status()

        media_id = response.json().get("id")
        if not media_id:
            raise RuntimeError(
                f"META | upload de mídia sem media_id no retorno: {response.text[:200]}"
            )
        logger.debug("META | mídia enviada com sucesso | media_id=%s", media_id)
        return media_id

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