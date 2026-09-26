"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Usuário Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     usuario_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "USUÁRIO" do EcoChatBot-MA.

Todas as classes herdam de `UsuarioException`, que por sua vez herda de
`EcoChatBotException`, garantindo:

    • status_code HTTP
    • error_code programático
    • detail para resposta JSON
    • método to_dict() para serialização

DOMÍNIO "USUÁRIO"
─────────────────
O usuário é o OPERADOR do sistema (atendente, supervisor, gerente,
administrador). Ele pertence a 1 tenant (empresa) e tem 1 nível de acesso.

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────┬─────────┬─────────────────────┐
    │ Classe                               │ Status  │ Quando usar         │
    ├──────────────────────────────────────┼─────────┼─────────────────────┤
    │ UsuarioException                     │ 500     │ Base                │
    │ UsuarioNaoEncontradoException        │ 404     │ Usuário não existe  │
    │ EmailJaCadastradoException           │ 409     │ E-mail duplicado    │
    │ UsernameJaCadastradoException        │ 409     │ Username duplicado  │
    │ SenhaFracaException                  │ 422     │ Senha não atende    │
    │ SenhaIncorretaException              │ 401     │ Senha atual errada  │
    │ UsuarioInativoException              │ 403     │ Usuário desativado  │
    │ UsuarioSemDepartamentoException      │ 422     │ Sem departamento    │
    └──────────────────────────────────────┴─────────┴─────────────────────┘

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções servem a QUALQUER canal e segmento.

USO
───
    from app.exceptions import UsuarioNaoEncontradoException

    if not user:
        raise UsuarioNaoEncontradoException(user_id=7)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "USUÁRIO"
# ═══════════════════════════════════════════════════════════════════════════


class UsuarioException(EcoChatBotException):
    """Classe BASE para todas as exceções do domínio "usuário"."""

    def __init__(
        self,
        message: str = 'Erro relacionado ao usuário',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'USUARIO_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE EXISTÊNCIA
# ═══════════════════════════════════════════════════════════════════════════


class UsuarioNaoEncontradoException(UsuarioException):
    """USUÁRIO NÃO ENCONTRADO. HTTP Status: 404"""

    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None) -> None:
        message = 'Usuário não encontrado'
        if user_id:
            message += f' (id={user_id})'
        elif email:
            message += f' (email={email})'

        super().__init__(
            message=message,
            status_code=404,
            error_code='USUARIO_NAO_ENCONTRADO',
        )


class EmailJaCadastradoException(UsuarioException):
    """E-MAIL JÁ CADASTRADO em outro usuário. HTTP Status: 409"""

    def __init__(self, email: Optional[str] = None) -> None:
        message = 'E-mail já cadastrado'
        if email:
            message += f': {email}'

        super().__init__(
            message=message,
            status_code=409,
            error_code='EMAIL_JA_CADASTRADO',
        )


class UsernameJaCadastradoException(UsuarioException):
    """USERNAME JÁ CADASTRADO em outro usuário. HTTP Status: 409"""

    def __init__(self, username: Optional[str] = None) -> None:
        message = 'Nome de usuário já cadastrado'
        if username:
            message += f': {username}'

        super().__init__(
            message=message,
            status_code=409,
            error_code='USERNAME_JA_CADASTRADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE SENHA
# ═══════════════════════════════════════════════════════════════════════════


class SenhaFracaException(UsuarioException):
    """SENHA NÃO ATENDE aos requisitos mínimos. HTTP Status: 422"""

    def __init__(self, motivo: str = 'Senha não atende aos requisitos mínimos') -> None:
        super().__init__(
            message=motivo,
            status_code=422,
            error_code='SENHA_FRACA',
        )


class SenhaIncorretaException(UsuarioException):
    """SENHA ATUAL INCORRETA (troca de senha). HTTP Status: 401"""

    def __init__(self) -> None:
        super().__init__(
            message='Senha atual incorreta',
            status_code=401,
            error_code='SENHA_INCORRETA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE ESTADO
# ═══════════════════════════════════════════════════════════════════════════


class UsuarioInativoException(UsuarioException):
    """USUÁRIO INATIVO (soft delete). HTTP Status: 403"""

    def __init__(self, user_id: Optional[int] = None) -> None:
        message = 'Usuário inativo'
        if user_id:
            message += f' (id={user_id})'

        super().__init__(
            message=message,
            status_code=403,
            error_code='USUARIO_INATIVO',
        )


class UsuarioSemDepartamentoException(UsuarioException):
    """USUÁRIO SEM DEPARTAMENTO (operação exige departamento). HTTP Status: 422"""

    def __init__(self, user_id: Optional[int] = None) -> None:
        message = 'Usuário não vinculado a um departamento'
        if user_id:
            message += f' (id={user_id})'

        super().__init__(
            message=message,
            status_code=422,
            error_code='USUARIO_SEM_DEPARTAMENTO',
        )


__all__ = [
    'UsuarioException',
    'UsuarioNaoEncontradoException',
    'EmailJaCadastradoException',
    'UsernameJaCadastradoException',
    'SenhaFracaException',
    'SenhaIncorretaException',
    'UsuarioInativoException',
    'UsuarioSemDepartamentoException',
]