"""
Exceções customizadas da aplicação — códigos de erro de negócio.
"""


class AppError(Exception):
    """Erro base da aplicação."""


# ── Atendimento ──────────────────────────────────────────────
class AtendimentoNotFound(AppError):
    pass


class AtendimentoInvalidStatus(AppError):
    pass


class AtendimentoPermissionDenied(AppError):
    pass


class AtendimentoAlreadyFinalized(AppError):
    pass


# ── Usuário ──────────────────────────────────────────────────
class UsuarioNotFound(AppError):
    pass


class UsuarioAlreadyExists(AppError):
    pass


class UsuarioInvalidPassword(AppError):
    pass


class UsuarioInactive(AppError):
    pass


class UsuarioPermissionDenied(AppError):
    pass


# ── Tenant / Cliente ─────────────────────────────────────────
class ClienteNotFound(AppError):
    pass


class ClientePermissionDenied(AppError):
    pass
