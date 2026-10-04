# app/adapters/__init__.py
"""
Módulo: adapters/__init__.py

Explicação:
Ponto de entrada do pacote de adaptadores de mensagem. Exporta o contrato
`BaseMessageAdapter`, as implementacoes por provedor e a fabrica que resolve
o adaptador correto pelo canal.

O escopo publico e deliberado: apenas o que existe no codigo e exportado.
Nao se exporta nome de classe inexistente, porque isso derruba o pacote
inteiro no import.
"""

from app.adapters.adapter_factory import (
    PROVEDOR_PADRAO,
    get_adapter,
    registrar,
    supported,
)
from app.adapters.base_message_adapter import BaseMessageAdapter
from app.adapters.providers.evolution_adapter import EvolutionAdapter
from app.adapters.providers.meta_cloud_adapter import MetaCloudAdapter
from app.adapters.providers.pabx_voip_adapter import PABXVoIPAdapter
from app.adapters.providers.telegram_adapter import TelegramAdapter

__all__ = [
    "BaseMessageAdapter",
    "EvolutionAdapter",
    "MetaCloudAdapter",
    "TelegramAdapter",
    "PABXVoIPAdapter",
    "get_adapter",
    "registrar",
    "supported",
    "PROVEDOR_PADRAO",
]