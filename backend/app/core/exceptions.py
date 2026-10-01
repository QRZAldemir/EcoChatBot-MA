"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Exceções Customizadas
───────────────────────────────────────────────────────────────────────────
@file     exceptions.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define exceções customizadas para o domínio do EcoChatBot-MA, permitindo
tratamento específico e mensagens de erro padronizadas.

REGRAS DE NEGÓCIO
─────────────────
    • Todas as exceções herdam de Exception ou HTTPException
    • Cada exceção possui um código único para referência
    • Mensagens são claras e acionáveis para o usuário final
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from fastapi import HTTPException, status
from typing import Any, Dict, List, Optional


class EcoChatBotException(Exception):
    """
    Exceção base para todas as exceções customizadas do EcoChatBot-MA.
    """
    
    def __init__(
        self,
        codigo: str,
        mensagem: str,
        status_code: int = 500,
        detalhes: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        self.codigo = codigo
        self.mensagem = mensagem
        self.status_code = status_code
        self.detalhes = detalhes
        super().__init__(mensagem)


# ==============================================================================
# EXCEÇÕES DE AUTENTICAÇÃO E AUTORIZAÇÃO
# ==============================================================================

class AuthenticationError(EcoChatBotException):
    """Erro de autenticação (token inválido, expirado, ausente)."""
    
    def __init__(self, mensagem: str = "Autenticação necessária", detalhes: Optional[Any] = None):
        super().__init__(
            codigo="AUTHENTICATION_ERROR",
            mensagem=mensagem,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detalhes=detalhes,
        )


class AuthorizationError(EcoChatBotException):
    """Erro de autorização (usuário não tem permissão para o recurso)."""
    
    def __init__(self, mensagem: str = "Acesso negado", detalhes: Optional[Any] = None):
        super().__init__(
            codigo="AUTHORIZATION_ERROR",
            mensagem=mensagem,
            status_code=status.HTTP_403_FORBIDDEN,
            detalhes=detalhes,
        )


# ==============================================================================
# EXCEÇÕES DE RECURSO
# ==============================================================================

class ResourceNotFoundError(EcoChatBotException):
    """Recurso não encontrado (404)."""
    
    def __init__(self, recurso: str = "Recurso", identificador: Optional[str] = None):
        mensagem = f"{recurso} não encontrado"
        if identificador:
            mensagem += f" (id: {identificador})"
        
        super().__init__(
            codigo="RESOURCE_NOT_FOUND",
            mensagem=mensagem,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ResourceAlreadyExistsError(EcoChatBotException):
    """Recurso já existe (conflito de unicidade)."""
    
    def __init__(self, recurso: str = "Recurso", campo: str = "identificador"):
        super().__init__(
            codigo="RESOURCE_ALREADY_EXISTS",
            mensagem=f"{recurso} já existe com este {campo}",
            status_code=status.HTTP_409_CONFLICT,
        )


# ==============================================================================
# EXCEÇÕES DE VALIDAÇÃO DE DOMÍNIO
# ==============================================================================

class BusinessRuleViolationError(EcoChatBotException):
    """Violação de regra de negócio."""
    
    def __init__(self, mensagem: str, detalhes: Optional[Any] = None):
        super().__init__(
            codigo="BUSINESS_RULE_VIOLATION",
            mensagem=mensagem,
            status_code=status.HTTP_400_BAD_REQUEST,
            detalhes=detalhes,
        )


class TenantIsolationError(EcoChatBotException):
    """Tentativa de acessar recurso de outro tenant (Anti-IDOR)."""
    
    def __init__(self, recurso: str = "Recurso"):
        super().__init__(
            codigo="TENANT_ISOLATION_VIOLATION",
            mensagem=f"Você não tem acesso a este {recurso}",
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ==============================================================================
# EXCEÇÕES DE INTEGRAÇÃO
# ==============================================================================

class IntegrationError(EcoChatBotException):
    """Erro em integração externa (WhatsApp, Telegram, etc.)."""
    
    def __init__(self, canal: str, mensagem: str, detalhes: Optional[Any] = None):
        super().__init__(
            codigo="INTEGRATION_ERROR",
            mensagem=f"Erro na integração com {canal}: {mensagem}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            detalhes=detalhes,
        )


class WebhookValidationError(EcoChatBotException):
    """Webhook recebido com dados inválidos ou token incorreto."""
    
    def __init__(self, mensagem: str = "Webhook inválido"):
        super().__init__(
            codigo="WEBHOOK_VALIDATION_ERROR",
            mensagem=mensagem,
            status_code=status.HTTP_400_BAD_REQUEST,
        )