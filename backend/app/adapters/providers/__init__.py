# app/adapters/providers/__init__.py
"""
Módulo: adapters/providers/__init__.py
"""

from app.adapters.providers.evolution_adapter import EvolutionAdapter
from app.adapters.providers.meta_cloud_adapter import MetaCloudAdapter
from app.adapters.providers.telegram_adapter import TelegramAdapter
from app.adapters.providers.pabx_voip_adapter import PABXVoIPAdapter

__all__ = [
    "EvolutionAdapter",
    "MetaCloudAdapter",
    "TelegramAdapter",
    "PABXVoIPAdapter",
]
