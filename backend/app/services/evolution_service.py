"""
app/services/evolution_service.py
──────────────────────────────────────────────────────────────────
Cliente HTTP para a Evolution API (self-hosted) ou EvoAI Cloud.

Variáveis de ambiente:
    EVOLUTION_API_URL     Base URL da instância (ex: http://localhost:8080)
    EVOLUTION_API_KEY     Chave de acesso
    EVOLUTION_AUTH_HEADER Nome do header de autenticação:
                          - "apikey"           → Evolution API self-hosted (padrão)
                          - "api_access_token" → EvoAI Cloud Platform
    WEBHOOK_SECRET        Token enviado pela Evolution p/ validar webhooks
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

EVOLUTION_API_URL    = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY    = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_AUTH_HEADER = os.getenv("EVOLUTION_AUTH_HEADER", "apikey")  # ou "api_access_token"
WEBHOOK_SECRET       = os.getenv("WEBHOOK_SECRET", "")


def _headers() -> dict:
    """
    Monta os headers de autenticação conforme o modo configurado:
      - Self-hosted Evolution API → "apikey"
      - EvoAI Cloud Platform      → "api_access_token"
    """
    return {
        EVOLUTION_AUTH_HEADER: EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }


def _log_erro(funcao: str, status: int, texto: str) -> None:
    logger.error("evolution_service | %s | HTTP %s | %s", funcao, status, texto[:200])


async def enviar_texto(instance: str, number: str, text: str) -> dict:
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=_headers(), json={"number": number, "text": text})
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("enviar_texto", e.response.status_code, e.response.text)
            raise
        except httpx.TimeoutException:
            logger.error("evolution_service | enviar_texto | timeout instancia=%s", instance)
            raise


async def enviar_midia(
    instance: str,
    number: str,
    media_url: str,
    caption: Optional[str] = None,
    mediatype: str = "document",
) -> dict:
    url = f"{EVOLUTION_API_URL}/message/sendMedia/{instance}"
    payload: dict = {"number": number, "mediatype": mediatype, "media": media_url}
    if caption:
        payload["caption"] = caption

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=_headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("enviar_midia", e.response.status_code, e.response.text)
            raise


async def enviar_lista(
    instance: str,
    number: str,
    title: str,
    description: str,
    button_text: str,
    sections: list,
    footer: Optional[str] = None,
) -> dict:
    """
    Envia uma lista interativa (sendList) via Evolution API.

    Estrutura das sections:
        [{"title": "Seção", "rows": [{"title": str, "description": str, "rowId": str}]}]

    O cliente recebe um menu com botão; ao selecionar, a Evolution devolve
    um webhook com listResponseMessage.singleSelectReply.selectedRowId.
    """
    url = f"{EVOLUTION_API_URL}/message/sendList/{instance}"
    payload = {
        "number": number,
        "title": title,
        "description": description,
        "buttonText": button_text,
        "footerText": footer or "",
        "sections": sections,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=_headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("enviar_lista", e.response.status_code, e.response.text)
            raise


async def enviar_template(
    instance: str,
    number: str,
    template_name: str,
    language: str,
    header_parameters: list,
    body_parameters: list,
) -> dict:
    url = f"{EVOLUTION_API_URL}/message/sendTemplate/{instance}"
    components = []
    if header_parameters:
        components.append({"type": "header", "parameters": header_parameters})
    if body_parameters:
        components.append({"type": "body", "parameters": body_parameters})

    payload = {
        "number": number,
        "name": template_name,
        "language": language,
        "components": components,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=_headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("enviar_template", e.response.status_code, e.response.text)
            raise


async def verificar_conexao(instance: str) -> dict:
    """Verifica se a instância está conectada ao WhatsApp."""
    url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(url, headers=_headers())
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("verificar_conexao", e.response.status_code, e.response.text)
            return {"state": "unknown"}


async def verificar_mensagem(instance: str, number: str, msg_id: str) -> dict:
    url = f"{EVOLUTION_API_URL}/message/findMessages/{instance}"
    payload = {"where": {"key": {"remoteJid": f"{number}@s.whatsapp.net", "id": msg_id}}}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=_headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            _log_erro("verificar_mensagem", e.response.status_code, e.response.text)
            raise


def _detectar_mediatype(url: str) -> str:
    u = url.lower()
    if any(u.endswith(e) for e in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "image"
    if any(u.endswith(e) for e in (".mp4", ".mov", ".avi")):
        return "video"
    if any(u.endswith(e) for e in (".mp3", ".ogg", ".aac")):
        return "audio"
    return "document"
