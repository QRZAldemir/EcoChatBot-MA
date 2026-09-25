"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Base Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     base_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define a HIERARQUIA BASE de exceções customizadas do EcoChatBot-Marcx.

Todas as exceções da aplicação herdam de `EcoChatBotException`, que
carrega:
    • message      → mensagem descritiva
    • status_code  → código HTTP (default: 500)
    • detail       → detalhes adicionais
    • error_code   → código programático (ex.: 'NOT_FOUND')
    • to_dict()    → serialização para resposta JSON

EXCEÇÕES DISPONÍVEIS
────────────────────
    • EcoChatBotException     → base (500)
    • ValidationException     → erros de validação (422)
    • NotFoundException       → recurso não encontrado (404)
    • UnauthorizedException   → autenticação falhou (401)
    • ForbiddenException      → permissão negada (403)
    • ConflictException       → conflito de recurso (409)
    • ServiceException        → erro em serviço (500)
    • RepositoryException     → erro em repositório (500)
    • DatabaseException       → erro de banco (500)
    • IntegrationException    → erro em integração (502)
    • FileUploadException     → erro no upload (400)
    • EmailException          → erro no envio de e-mail (500)

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções são agnósticas de canal e segmento. Funcionam igualmente
em WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em qualquer
segmento de negócio.

USO
───
    from app.exceptions.base_exceptions import (
        NotFoundException,
        ValidationException,
    )

    # Exemplo 1: recurso não encontrado
    raise NotFoundException(resource='Usuário', identifier='123')

    # Exemplo 2: validação com campos
    raise ValidationException(
        message='Dados inválidos',
        fields={'email': 'E-mail já cadastrado'}
    )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE
# ═══════════════════════════════════════════════════════════════════════════


class EcoChatBotException(Exception):
    """
    Classe BASE para todas as exceções customizadas do EcoChatBot-Marcx.

    Attributes:
        message:     Mensagem descritiva do erro.
        status_code: Código HTTP associado (default: 500).
        detail:      Detalhes adicionais (default: message).
        error_code:  Código programático do erro (default: 'INTERNAL_ERROR').
    """

    def __init__(
        self,
        message: str = 'Ocorreu um erro no EcoChatBot',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        self.error_code = error_code or 'INTERNAL_ERROR'
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Serializa a exceção para resposta JSON."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'detail': self.detail,
            'status_code': self.status_code,
        }

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})'


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE VALIDAÇÃO E RECURSOS
# ═══════════════════════════════════════════════════════════════════════════


class ValidationException(EcoChatBotException):
    """
    Erro de VALIDAÇÃO de dados.

    HTTP Status: 422 Unprocessable Entity

    Attributes:
        fields: Dicionário com erros por campo (ex.: {'email': 'inválido'}).
    """

    def __init__(
        self,
        message: str = 'Erro de validação',
        detail: Optional[str] = None,
        fields: Optional[dict] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            detail=detail,
            error_code='VALIDATION_ERROR',
        )
        self.fields = fields or {}

    def to_dict(self) -> dict:
        data = super().to_dict()
        if self.fields:
            data['fields'] = self.fields
        return data


class NotFoundException(EcoChatBotException):
    """
    Erro para RECURSO NÃO ENCONTRADO.

    HTTP Status: 404 Not Found
    """

    def __init__(self, resource: str = 'Recurso', identifier: Optional[str] = None) -> None:
        message = f'{resource} não encontrado'
        if identifier:
            message += f': {identifier}'

        super().__init__(
            message=message,
            status_code=404,
            error_code='NOT_FOUND',
        )


class ConflictException(EcoChatBotException):
    """
    Erro de CONFLITO (ex.: recurso já existe).

    HTTP Status: 409 Conflict
    """

    def __init__(self, message: str = 'Conflito de recursos') -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code='CONFLICT',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE AUTENTICAÇÃO E AUTORIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class UnauthorizedException(EcoChatBotException):
    """
    Erro de AUTENTICAÇÃO (usuário não autenticado).

    HTTP Status: 401 Unauthorized
    """

    def __init__(self, message: str = 'Não autorizado') -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code='UNAUTHORIZED',
        )


class ForbiddenException(EcoChatBotException):
    """
    Erro de PERMISSÃO (usuário autenticado mas sem acesso).

    HTTP Status: 403 Forbidden
    """

    def __init__(self, message: str = 'Acesso proibido') -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code='FORBIDDEN',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE SERVIÇOS E REPOSITÓRIOS
# ═══════════════════════════════════════════════════════════════════════════


class ServiceException(EcoChatBotException):
    """
    Erro em SERVIÇO de negócio.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, message: str = 'Erro no serviço', service_name: Optional[str] = None) -> None:
        if service_name:
            message = f'Erro no serviço {service_name}: {message}'

        super().__init__(
            message=message,
            status_code=500,
            error_code='SERVICE_ERROR',
        )


class RepositoryException(EcoChatBotException):
    """
    Erro em REPOSITÓRIO (acesso ao banco).

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, message: str = 'Erro no repositório', operation: Optional[str] = None) -> None:
        if operation:
            message = f'Erro na operação {operation}: {message}'

        super().__init__(
            message=message,
            status_code=500,
            error_code='REPOSITORY_ERROR',
        )


class DatabaseException(EcoChatBotException):
    """
    Erro específico do BANCO DE DADOS.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, message: str = 'Erro no banco de dados', db_type: Optional[str] = None) -> None:
        if db_type:
            message = f'Erro no {db_type}: {message}'

        super().__init__(
            message=message,
            status_code=500,
            error_code='DATABASE_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE INTEGRAÇÕES E ARQUIVOS
# ═══════════════════════════════════════════════════════════════════════════


class IntegrationException(EcoChatBotException):
    """
    Erro em INTEGRAÇÃO externa (WhatsApp, Telegram, etc.).

    HTTP Status: 502 Bad Gateway
    """

    def __init__(self, message: str = 'Erro na integração', integration_name: Optional[str] = None) -> None:
        if integration_name:
            message = f'Erro na integração com {integration_name}: {message}'

        super().__init__(
            message=message,
            status_code=502,
            error_code='INTEGRATION_ERROR',
        )


class FileUploadException(EcoChatBotException):
    """
    Erro no UPLOAD de arquivo.

    HTTP Status: 400 Bad Request
    """

    def __init__(self, message: str = 'Erro no upload do arquivo') -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code='FILE_UPLOAD_ERROR',
        )


class EmailException(EcoChatBotException):
    """
    Erro no ENVIO DE E-MAIL.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, message: str = 'Erro no envio de email') -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code='EMAIL_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'EcoChatBotException',
    'ValidationException',
    'NotFoundException',
    'ConflictException',
    'UnauthorizedException',
    'ForbiddenException',
    'ServiceException',
    'RepositoryException',
    'DatabaseException',
    'IntegrationException',
    'FileUploadException',
    'EmailException',
]