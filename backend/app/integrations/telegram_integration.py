# app/integrations/telegram_integration.py
"""
Módulo: telegram_integration.py

Explicação:
Responsável por conectar a aplicação à API do Telegram. 
Mapeia os métodos nativos da API para os métodos da nossa interface base, 
abstraindo as particularidades da plataforma, como o uso de chat_id numérico 
e métodos específicos para diferentes tipos de mídia.

Funcionalidades:
- send_text_message: Invoca o método 'sendMessage' da API do Telegram.
- send_media_message: Roteia dinamicamente para 'sendPhoto' ou 'sendDocument' baseado no tipo de mídia.
- parse_incoming_webhook: Extrai dados do objeto 'message' do payload de update do Telegram.
"""

import httpx
from .base import BaseChannelIntegration
from app.core.config import settings
from typing import Dict, Any

class TelegramIntegration(BaseChannelIntegration):
    """Integração específica para o canal Telegram via Bot API."""

    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Envia mensagem de texto para um chat_id específico."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/sendMessage", json={"chat_id": chat_id, "text": text})
            return response.json()

    async def send_media_message(self, chat_id: str, media_url: str, media_type: str) -> Dict[str, Any]:
        """Envia mídia, roteando para o método correto (sendPhoto ou sendDocument)."""
        method = "sendPhoto" if media_type == "image" else "sendDocument"
        media_key = "photo" if media_type == "image" else "document"
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/{method}", json={"chat_id": chat_id, media_key: media_url})
            return response.json()

    def parse_incoming_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai remetente e texto do payload de update do Telegram."""
        message = payload.get("message", {})
        return {
            "sender": str(message.get("from", {}).get("id")),
            "text": message.get("text", ""),
            "type": "text" if "text" in message else "media"
        }