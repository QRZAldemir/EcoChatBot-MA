"""
================================================================================
FÁBRICA DE HANDLERS - CRIAÇÃO DINÂMICA DE HANDLERS
================================================================================
Arquivo: bot_handlers/handler_factory.py
Propósito: Criar o handler correto baseado no departamento e configuração

DESENVOLVEDOR: Aldemir Queiroz da Silva
DATA: 2026-08-16

PADRÃO DE PROJETO: Factory Pattern

SINTAXE:
    - Método estático para criar handlers
    - Baseado no tipo de departamento
    - Carrega configurações do cliente
    - Retorna instância do handler apropriado

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento
from .base_handler import DepartamentoHandler
from .atendimento_handler import AtendimentoHandler
from .agendamento_handler import AgendamentoHandler
from .pedidos_handler import PedidosHandler
from typing import Optional, Dict, Type


class HandlerFactory:
    """
    FÁBRICA DE HANDLERS
    
    Responsabilidades:
        1. Criar o handler correto para o departamento
        2. Carregar configurações do cliente
        3. Injetar dependências
        4. Retornar instância configurada
    
    PADRÃO FACTORY: Centraliza a criação de objetos
    """
    
    # Mapeamento departamento -> Handler (Registro de handlers)
    _handlers_registry: Dict[str, Type[DepartamentoHandler]] = {
        "ATENDIMENTO": AtendimentoHandler,
        "AGENDAMENTO": AgendamentoHandler,
        "PEDIDOS": PedidosHandler,
        # Adicionar novos handlers conforme necessidade
        # "PAGAMENTOS": PagamentosHandler,
        # "FINANCEIRO": FinanceiroHandler,
        # "RH": RHHandler,
        # "SUPORTE": SuporteHandler,
    }
    
    @classmethod
    def registrar_handler(cls, nome: str, handler_class: Type[DepartamentoHandler]) -> None:
        """
        Registra um novo handler na fábrica
        
        EXTENSIBILIDADE: Permite adicionar novos handlers dinamicamente
        
        EXEMPLO:
            HandlerFactory.registrar_handler("FROTAS", FrotaHandler)
        """
        cls._handlers_registry[nome.upper()] = handler_class
    
    @classmethod
    def criar_handler(
        cls,
        session: Session,
        departamento: str,
        empresa_id: int
    ) -> Optional[DepartamentoHandler]:
        """
        Cria o handler apropriado baseado no departamento
        
        POLIMORFISMO: Retorna diferentes handlers
        
        Args:
            session: Sessão do banco de dados
            departamento: Nome do departamento
            empresa_id: ID da empresa (tenant)
        
        RETORNO:
            Instância do handler configurada
        """
        # Busca a classe do handler
        handler_class = cls._handlers_registry.get(departamento.upper())
        
        if not handler_class:
            # Handler padrão (fallback)
            return None
        
        # Cria instância com injeção de dependências
        return handler_class(session, empresa_id)
    
    @classmethod
    def criar_handler_por_atendimento(
        cls,
        session: Session,
        atendimento: Atendimento
    ) -> Optional[DepartamentoHandler]:
        """
        Cria handler baseado no atendimento atual
        
        Útil quando o departamento é definido dinamicamente
        """
        # TODO: Buscar departamento do atendimento
        departamento = atendimento.departamento_atual
        
        # TODO: Buscar empresa_id do atendimento
        empresa_id = atendimento.empresa_id
        
        return cls.criar_handler(session, departamento, empresa_id)
    
    @classmethod
    def listar_handlers_disponiveis(cls) -> List[str]:
        """
        Lista todos os handlers registrados
        
        Útil para mostrar opções de departamentos disponíveis
        """
        return list(cls._handlers_registry.keys())