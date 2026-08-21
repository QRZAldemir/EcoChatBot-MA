"""
================================================================================
MÓDULO: bot_handlers (Handlers OOP para Máquina de Estados)
================================================================================

Exports principais para uso em routers e dependências.

Padrão de Handler:
  1. Herda de DepartamentoHandler
  2. Implementa processar() com lógica específica do departamento
  3. Reutiliza métodos base: _enviar_texto(), _enviar_lista(), _guardar_contexto()
  4. Responsabilidade única: Gerenciar fluxo de seu departamento
"""

from .base_handler import DepartamentoHandler
from .evolution_client import EvolutionApiClient
from .bot_machine import BotMáquinaEstados
from .atendimento import AtendimentoHandler
from .agendamento import AgendamentoHandler

__all__ = [
    "DepartamentoHandler",
    "EvolutionApiClient",
    "BotMáquinaEstados",
    "AtendimentoHandler",
    "AgendamentoHandler",
]
