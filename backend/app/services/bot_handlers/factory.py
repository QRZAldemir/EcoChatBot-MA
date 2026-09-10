"""
================================================================================
FÁBRICA DE HANDLERS (FACTORY PATTERN)
================================================================================
DESENVOLVEDOR: Aldemir Queiroz
DATA: 2026-08-16
PROPÓSITO: Centralizar a criação de handlers, evitando if/elif complexos.
================================================================================
"""
from typing import Type
from sqlalchemy.orm import Session

# Importe aqui os handlers específicos do seu projeto
# from .agendamento_handler import AgendamentoHandler
# from .suporte_handler import SuporteHandler
from .core import DepartamentoHandler


class HandlerFactory:
    """
    Factory Pattern para instanciar o handler correto baseado no departamento.
    """
    
    # Registro de handlers disponíveis
    _handlers: dict[str, Type[DepartamentoHandler]] = {
        # "AGENDAMENTO": AgendamentoHandler,
        # "SUPORTE": SuporteHandler,
        # "PADRAO": DefaultHandler,
    }

    @classmethod
    def registrar_handler(cls, departamento: str, handler_class: Type[DepartamentoHandler]) -> None:
        """Permite registrar novos handlers dinamicamente."""
        cls._handlers[departamento.upper()] = handler_class

    @classmethod
    def create_handler(cls, departamento: str, session: Session) -> DepartamentoHandler:
        """
        Cria e retorna a instância do handler solicitado.
        
        Args:
            departamento: Nome do departamento (ex: "AGENDAMENTO")
            session: Sessão do banco de dados para injetar no handler
            
        Raises:
            ValueError: Se o departamento não estiver registrado.
        """
        departamento = departamento.upper()
        handler_class = cls._handlers.get(departamento)
        
        if not handler_class:
            # Fallback para um handler padrão ou erro
            raise ValueError(f"Handler não encontrado para o departamento: {departamento}")
        
        return handler_class(session)