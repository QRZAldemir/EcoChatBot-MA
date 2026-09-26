# app/integrations/__init__.py
"""
Módulo: __init__.py

Explicação:
Ponto de entrada do pacote `integrations`. Expõe apenas as integrações que
realmente existem no código, para que `import app.integrations` funcione e o
escopo público do pacote seja explícito.

Funcionalidades:
- Importação Centralizada: carrega as classes de integração implementadas.
- Controle de Escopo: `__all__` define o que é público.
- Honestidade de escopo: as integrações ainda não implementadas são listadas
  como ausentes, sem exportar nomes que não existem.

INTEGRAÇÕES IMPLEMENTADAS:
- Telegram  (app/integrations/telegram_integration.py)
- Discord   (app/integrations/discord_integration.py)
- Base      (app/integrations/base.py)

INTEGRAÇÕES NÃO IMPLEMENTADAS (arquivos com 0 bytes, sem nenhuma classe):
- WhatsApp  (app/integrations/whatsapp_integration.py)
- Instagram (app/integrations/instagram_integration.py)
- Facebook  (app/integrations/facebook_integration.py)
- MicroSIP  (app/integrations/microsip_integration.py)
- OCR       (app/integrations/ocr_integration.py)
- TTS       (app/integrations/tts_integration.py)

Essas seis NÃO são exportadas de propósito. Antes, este arquivo importava os
oito nomes e o pacote inteiro falhava ao ser carregado, derrubando 9 módulos.
Não foram criadas classes vazias para "fazer passar": o contrato delas
(fontes, credenciais, webhooks) ainda não foi definido.
"""

from .base import BaseChannelIntegration, BaseUtilityIntegration
from .discord_integration import DiscordIntegration
from .telegram_integration import TelegramIntegration

__all__ = [
    "BaseChannelIntegration",
    "BaseUtilityIntegration",
    "TelegramIntegration",
    "DiscordIntegration",
]
