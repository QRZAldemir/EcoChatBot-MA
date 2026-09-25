# app/integrations/discord_integration.py
"""
Módulo: discord_integration.py

Explicação:
Gerencia a interação com a API REST do Discord. 
Diferente de outros canais, o Discord utiliza tokens de Bot e requer que as mensagens 
sejam enviadas para channel_id. O módulo adapta o envio de mídias para o formato 
de Embeds ou links diretos, conforme as diretrizes da plataforma.

Funcionalidades:
- send_text_message: Envia conteúdo textual para um canal específico (channel_id).
- send_media_message: Formata o envio de mídia utilizando a estrutura de Embeds ou Markdown.
- parse_incoming_webhook: Processa payloads de interações ou mensagens do Discord.
"""

import httpx
from .base import BaseChannelIntegration
from app.core.config import settings
from typing import Dict, Any

class DiscordIntegration(BaseChannelIntegration):
    """Integração específica para o canal Discord via API REST."""

    def __init__(self):
        self.base_url = "https://discord.com/api/v10"
        self.token = settings.DISCORD_BOT_TOKEN
        self.headers = {"Authorization": f"Bot {self.token}", "Content-Type": "application/json"}

    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Envia mensagem de texto para um channel_id do Discord."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/channels/{chat_id}/messages", json={"content": text}, headers=self.headers)
            return response.json()

    async def send_media_message(self, chat_id: str, media_url: str, media_type: str) -> Dict[str, Any]:
        """Envia mídia utilizando Embeds (para imagens) ou links formatados."""
        embed = {"embeds": [{"image": {"url": media_url}}] if media_type == "image" else {"description": f"[Arquivo]({media_url})"}}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/channels/{chat_id}/messages", json=embed, headers=self.headers)
            return response.json()

    def parse_incoming_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados de interações ou mensagens do payload do Discord."""
        if payload.get("type") == 2: 
            return {
                "sender": payload.get("member", {}).get("user", {}).get("id"), 
                "text": payload.get("content", ""), 
                "type": "text"
            }
        return {}