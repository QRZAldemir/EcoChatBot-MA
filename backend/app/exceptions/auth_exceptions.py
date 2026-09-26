"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Auth Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     auth_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "AUTENTICAÇÃO E AUTORIZAÇÃO"
do EcoChatBot-MA.

Todas as classes herdam de `AuthException`, que por sua vez herda de
`EcoChatBotException`, garantindo:

    • status_code HTTP
    • error_code programático
    • detail para resposta JSON
    • método to_dict() para serialização

DOMÍNIO "AUTH"
──────────────
Autenticação e autorização envolvem:
    • Login (email + senha)
    • Refresh de token JWT
    • Validação de token expirado
    • Revogação de token (logout)
    • Permissões (RBAC)
    • Níveis de acesso

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────┬─────────┬─────────────────────┐
    │ Classe                               │ Status  │ Quando usar         │
    ├──────────────────────────────────────┼─────────┼─────────────────────┤
    │ AuthException                        │ 500     │ Base                │
    │ CredenciaisInvalidasException        │ 401     │ Login falhou        │
    │ TokenExpiradoException               │ 401     │ JWT expirado        │
    │ TokenInvalidoException               │ 401     │ JWT malformado      │
    │ TokenRevogadoException               │ 401     │ JWT na blacklist    │
    │ SessaoExpiradaException              │ 401     │ Sessão inválida     │
    │ PermissaoNegadaException             │ 403     │ Usuário sem acesso  │
    │ NivelInsuficienteException           │ 403     │ Nível insuficiente  │
    │ EmailNaoVerificadoException          │ 403     │ E-mail não verif.   │
    │ ContaInativaException                │ 403     │ Conta desativada    │
    │ ContaBloqueadaException              │ 423     │ Muitas tentativas   │
    └──────────────────────────────────────┴─────────┴─────────────────────┘

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções servem a QUALQUER canal (WhatsApp, Telegram, Discord,
Facebook, Instagram, PABX) e a QUALQUER segmento de negócio.

USO
───
    from app.exceptions import CredenciaisInvalidasException

    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        raise CredenciaisInvalidasException()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "AUTH"
# ═══════════════════════════════════════════════════════════════════════════


class AuthException(EcoChatBotException):
    """
    Classe BASE para todas as exceções do domínio "auth".

    Herda de `EcoChatBotException` (default status_code=500).
    """

    def __init__(
        self,
        message: str = 'Erro de autenticação',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'AUTH_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE CREDENCIAIS (LOGIN)
# ═══════════════════════════════════════════════════════════════════════════


class CredenciaisInvalidasException(AuthException):
    """
    CREDENCIAIS INVÁLIDAS (e-mail ou senha errados).

    HTTP Status: 401 Unauthorized

    ⚠️ SEGURANÇA: NUNCA revele se o e-mail existe ou não.
    Sempre use a mesma mensagem genérica: "Credenciais inválidas".

    Exemplo:
        raise CredenciaisInvalidasException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Credenciais inválidas',
            status_code=401,
            error_code='CREDENCIAIS_INVALIDAS',
        )


class ContaBloqueadaException(AuthException):
    """
    Conta BLOQUEADA por excesso de tentativas.

    HTTP Status: 423 Locked

    Exemplo:
        raise ContaBloqueadaException(tentativas=5, minutos=15)
    """

    def __init__(self, tentativas: int = 5, minutos: int = 15) -> None:
        super().__init__(
            message=f'Conta bloqueada após {tentativas} tentativas. Tente novamente em {minutos} minutos.',
            status_code=423,
            error_code='CONTA_BLOQUEADA',
        )


class ContaInativaException(AuthException):
    """
    Conta está INATIVA (soft delete ou não ativada).

    HTTP Status: 403 Forbidden

    Exemplo:
        raise ContaInativaException(email='joao@marcx.com')
    """

    def __init__(self, email: Optional[str] = None) -> None:
        message = 'Conta inativa'
        if email:
            message += f': {email}'

        super().__init__(
            message=message,
            status_code=403,
            error_code='CONTA_INATIVA',
        )


class EmailNaoVerificadoException(AuthException):
    """
    E-mail NÃO VERIFICADO pelo usuário.

    HTTP Status: 403 Forbidden

    Exemplo:
        raise EmailNaoVerificadoException('joao@marcx.com')
    """

    def __init__(self, email: Optional[str] = None) -> None:
        message = 'E-mail não verificado'
        if email:
            message += f': {email}. Verifique sua caixa de entrada.'

        super().__init__(
            message=message,
            status_code=403,
            error_code='EMAIL_NAO_VERIFICADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE TOKEN (JWT)
# ═══════════════════════════════════════════════════════════════════════════


class TokenExpiradoException(AuthException):
    """
    TOKEN JWT EXPIRADO.

    HTTP Status: 401 Unauthorized

    Exemplo:
        raise TokenExpiradoException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Token expirado. Faça login novamente.',
            status_code=401,
            error_code='TOKEN_EXPIRADO',
        )


class TokenInvalidoException(AuthException):
    """
    TOKEN JWT MALFORMADO ou com assinatura inválida.

    HTTP Status: 401 Unauthorized

    Exemplo:
        raise TokenInvalidoException()
    """

    def __init__(self, message: str = 'Token inválido') -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code='TOKEN_INVALIDO',
        )


class TokenRevogadoException(AuthException):
    """
    TOKEN JWT REVOGADO (presente na blacklist de logout).

    HTTP Status: 401 Unauthorized

    Exemplo:
        raise TokenRevogadoException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Token revogado. Faça login novamente.',
            status_code=401,
            error_code='TOKEN_REVOGADO',
        )


class TokenAusenteException(AuthException):
    """
    Nenhum token foi enviado no header Authorization.

    HTTP Status: 401 Unauthorized

    Exemplo:
        raise TokenAusenteException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Token de autenticação ausente',
            status_code=401,
            error_code='TOKEN_AUSENTE',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE SESSÃO
# ═══════════════════════════════════════════════════════════════════════════


class SessaoExpiradaException(AuthException):
    """
    SESSÃO EXPIRADA (por inatividade ou tempo máximo).

    HTTP Status: 401 Unauthorized

    Exemplo:
        raise SessaoExpiradaException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Sessão expirada. Faça login novamente.',
            status_code=401,
            error_code='SESSAO_EXPIRADA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE PERMISSÃO (RBAC)
# ═══════════════════════════════════════════════════════════════════════════


class PermissaoNegadaException(AuthException):
    """
    PERMISSÃO NEGADA — usuário autenticado mas sem acesso.

    HTTP Status: 403 Forbidden

    Exemplo:
        raise PermissaoNegadaException(recurso='usuarios:delete')
    """

    def __init__(self, recurso: Optional[str] = None) -> None:
        message = 'Permissão negada'
        if recurso:
            message += f' para: {recurso}'

        super().__init__(
            message=message,
            status_code=403,
            error_code='PERMISSAO_NEGADA',
        )


class NivelInsuficienteException(AuthException):
    """
    NÍVEL DE ACESSO INSUFICIENTE para a operação.

    HTTP Status: 403 Forbidden

    Exemplo:
        raise NivelInsuficienteException(
            nivel_atual='atendente',
            nivel_necessario='administrador'
        )
    """

    def __init__(
        self,
        nivel_atual: Optional[str] = None,
        nivel_necessario: Optional[str] = None,
    ) -> None:
        message = 'Nível de acesso insuficiente'
        if nivel_atual and nivel_necessario:
            message += f'. Você é "{nivel_atual}" e precisa ser "{nivel_necessario}".'

        super().__init__(
            message=message,
            status_code=403,
            error_code='NIVEL_INSUFICIENTE',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'AuthException',
    'CredenciaisInvalidasException',
    'ContaBloqueadaException',
    'ContaInativaException',
    'EmailNaoVerificadoException',
    'TokenExpiradoException',
    'TokenInvalidoException',
    'TokenRevogadoException',
    'TokenAusenteException',
    'SessaoExpiradaException',
    'PermissaoNegadaException',
    'NivelInsuficienteException',
]