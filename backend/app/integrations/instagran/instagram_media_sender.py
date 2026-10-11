# ==============================================================================
# ARQUIVO.....: whatsapp_media_sender.py
# PROJETO.....: EcoChatBot-MA
# MÓDULO......: Camada de envio de mídias via Meta Cloud API
# VERSÃO......: 1.0.0
# Aldemir Queiroz da Silva 
# DATA........: 10/10/2026
# ==============================================================================
# DESCRIÇÃO...:
# Encapsula a lógica de envio de mídias, aplicando as restrições da Graph API:
#   - ``caption`` é aceito APENAS para ``image`` e ``video``.
#   - ``audio`` exige upload prévio (POST /{phone_id}/media) para obtenção
#     de ``media_id``; URL pública direta é rejeitada (HTTP 400).
#   - ``document`` aceita ``caption`` e ``filename``.
# ==============================================================================
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Tipos de mídia que aceitam o parâmetro "caption" segundo a documentação Meta.
_CAPTION_ALLOWED_TYPES = frozenset({"image", "video", "document"})


class WhatsAppMediaSender:
    """Cliente de envio de mídias para WhatsApp Business via Graph API."""

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._phone_id = phone_number_id
        self._token = access_token
        self._timeout = timeout
        self._base_url = f"{GRAPH_API_BASE}/{phone_number_id}"

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def send_image(
        self,
        recipient: str,
        *,
        url: str | None = None,
        media_id: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        """Envia imagem. Aceita ``caption``."""
        media_ref = self._build_media_ref(url=url, media_id=media_id)
        if caption:
            media_ref["caption"] = caption
        return await self._post_message(recipient, "image", {"image": media_ref})

    async def send_video(
        self,
        recipient: str,
        *,
        url: str | None = None,
        media_id: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        """Envia vídeo. Aceita ``caption``."""
        media_ref = self._build_media_ref(url=url, media_id=media_id)
        if caption:
            media_ref["caption"] = caption
        return await self._post_message(recipient, "video", {"video": media_ref})

    async def send_document(
        self,
        recipient: str,
        *,
        url: str | None = None,
        media_id: str | None = None,
        filename: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        """Envia documento. Aceita ``caption`` e ``filename``."""
        media_ref = self._build_media_ref(url=url, media_id=media_id)
        if filename:
            media_ref["filename"] = filename
        if caption:
            media_ref["caption"] = caption
        return await self._post_message(
            recipient, "document", {"document": media_ref}
        )

    async def send_audio(
        self,
        recipient: str,
        *,
        url: str | None = None,
        media_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Envia áudio.

        **Restrição da Meta**: ``caption`` NÃO é aceito para áudio.
        Se ``media_id`` não for fornecido, realiza upload prévio
        obrigatório a partir da ``url``.
        """
        if not media_id:
            if not url:
                raise ValueError("É obrigatório fornecer 'url' ou 'media_id'.")
            media_id = await self.upload_media(url, media_type="audio")

        return await self._post_message(
            recipient, "audio", {"audio": {"id": media_id}}
        )

    # ------------------------------------------------------------------
    # Upload prévio (obrigatório para áudio)
    # ------------------------------------------------------------------

    async def upload_media(
        self,
        file_url: str,
        *,
        media_type: str = "audio",
    ) -> str:
        """
        Realiza upload de mídia para a Meta e retorna o ``media_id``.

        Endpoint: ``POST /{phone_number_id}/media``
        """
        upload_url = f"{self._base_url}/media"
        form_data = {
            "messaging_product": "whatsapp",
            "type": media_type,
            "link": file_url,
        }
        headers = {"Authorization": f"Bearer {self._token}"}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                upload_url, data=form_data, headers=headers
            )
            response.raise_for_status()
            data = response.json()

        media_id = data.get("id")
        if not media_id:
            raise RuntimeError(
                f"Upload de mídia falhou — resposta inesperada: {data}"
            )
        logger.info("Upload concluído: media_id=%s (type=%s)", media_id, media_type)
        return media_id

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    @staticmethod
    def _build_media_ref(
        *, url: str | None, media_id: str | None
    ) -> dict[str, str]:
        if media_id:
            return {"id": media_id}
        if url:
            return {"link": url}
        raise ValueError("É obrigatório fornecer 'url' ou 'media_id'.")

    async def _post_message(
        self,
        recipient: str,
        msg_type: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self._base_url}/messages"
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": msg_type,
            **body,
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()