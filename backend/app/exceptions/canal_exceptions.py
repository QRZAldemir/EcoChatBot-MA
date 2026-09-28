"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Exceções do domínio Canal
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal_exceptions.py
@module   Backend / App / Exceptions / Canal
@author   Aldemir Queiroz
@since    2026
@version  3.0.0
───────────────────────────────────────────────────────────────────────────

HIERARQUIA
──────────
    Exception
      └── EcoChatBotError
            ├── RecursoNaoEncontradoError  (404)
            ├── RecursoInvalidoError        (422)
            ├── AcessoNegadoError           (403)
            ├── LimiteCotaExcedidoError     (402)
            └── CanalException (agrupador semântico)
                  ├── CanalNaoEncontradoError
                  ├── CanalNomeDuplicadoError
                  ├── CanalTipoInvalidoError
                  ├── CanalConfiguracaoInvalidaError
                  ├── CanalWebhookError
                  └── CanalSemTelefoneError
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations


# ══════════════════════════════════════════════════════════════════════════
# BASE
# ══════════════════════════════════════════════════════════════════════════
class EcoChatBotError(Exception):
    """Base de todas as exceções de domínio do EcoChatBot-MA."""
    http_status: int = 500
    codigo: str = "eco_erro_generico"

    def __init__(self, mensagem: str, *, codigo: str | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo


# ══════════════════════════════════════════════════════════════════════════
# GENÉRICAS
# ══════════════════════════════════════════════════════════════════════════
class RecursoNaoEncontradoError(EcoChatBotError):
    """Recurso não existe OU pertence a outro tenant (Anti-IDOR)."""
    http_status = 404
    codigo = "recurso_nao_encontrado"


class RecursoInvalidoError(EcoChatBotError):
    """Payload inválido, violação de regra de negócio ou unicidade."""
    http_status = 422
    codigo = "recurso_invalido"


class AcessoNegadoError(EcoChatBotError):
    """Tentativa de acesso cross-tenant ou falta de `empresa_id`."""
    http_status = 403
    codigo = "acesso_negado"


class LimiteCotaExcedidoError(EcoChatBotError):
    """Plano SaaS do tenant não permite mais recursos."""
    http_status = 402
    codigo = "limite_cota_excedido"


# ══════════════════════════════════════════════════════════════════════════
# ESPECÍFICAS DE CANAL
# ══════════════════════════════════════════════════════════════════════════
class CanalException(EcoChatBotError):
    """Agrupador semântico para exceções de canal."""
    codigo = "canal_erro_generico"


class CanalNaoEncontradoError(RecursoNaoEncontradoError, CanalException):
    codigo = "canal_nao_encontrado"


class CanalNomeDuplicadoError(RecursoInvalidoError, CanalException):
    codigo = "canal_nome_duplicado"


class CanalTipoInvalidoError(RecursoInvalidoError, CanalException):
    codigo = "canal_tipo_invalido"


class CanalConfiguracaoInvalidaError(RecursoInvalidoError, CanalException):
    codigo = "canal_configuracao_invalida"


class CanalWebhookError(RecursoInvalidoError, CanalException):
    codigo = "canal_webhook_invalido"


class CanalSemTelefoneError(RecursoInvalidoError, CanalException):
    """Canal sem `telefone_id` — recusa com 403 conforme regra de negócio."""
    http_status = 403
    codigo = "canal_sem_telefone"


__all__ = [
    "EcoChatBotError",
    "RecursoNaoEncontradoError",
    "RecursoInvalidoError",
    "AcessoNegadoError",
    "LimiteCotaExcedidoError",
    "CanalException",
    "CanalNaoEncontradoError",
    "CanalNomeDuplicadoError",
    "CanalTipoInvalidoError",
    "CanalConfiguracaoInvalidaError",
    "CanalWebhookError",
    "CanalSemTelefoneError",
]