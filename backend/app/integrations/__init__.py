# app/integrations/__init__.py
"""
Módulo: __init__.py

Explicação:
Atua como o ponto de entrada e inicialização do pacote `integrations`. 
Sua função é centralizar as importações, expondo as classes de integração 
de forma limpa para o restante da aplicação.

Funcionalidades:
- Importação Centralizada: Carrega todas as classes de integração em memória.
- Controle de Escopo: Define explicitamente as classes públicas via __all__, prevenindo exportações acidentais.
"""

from .whatsapp_integration import WhatsAppIntegration
from .telegram_integration import TelegramIntegration
from .discord_integration import DiscordIntegration
from .instagram_integration import InstagramIntegration
from .facebook_integration import FacebookIntegration
from .microsip_integration import MicroSIPIntegration
from .ocr_integration import OCRIntegration
from .tts_integration import TTSIntegration

__all__ = [
    "WhatsAppIntegration", "TelegramIntegration", "DiscordIntegration",
    "InstagramIntegration", "FacebookIntegration", "MicroSIPIntegration",
    "OCRIntegration", "TTSIntegration"
]