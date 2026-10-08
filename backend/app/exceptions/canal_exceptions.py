"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Exceções do domínio Canal
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal_exceptions.py
@module   Backend / App / Exceptions / Canal
@author   Aldemir Queiroz
@since    2026
@version  3.1.0 (Expandido para suportar LSP de Integração/Runtime)
───────────────────────────────────────────────────────────────────────────

HIERARQUIA
──────────
    Exception
      └── EcoChatBotError
            ├── RecursoNaoEncontradoError  (404)
            ├── RecursoInvalidoError       (422)
            ├── AcessoNegadoError          (403)
            ├── LimiteCotaExcedidoError    (402)
            │
            └── CanalException (agrupador semântico de CANAL)
                  │
                  ├── [SUB-DOMÍNIO: CRUD / GESTÃO]
                  │     ├── CanalNaoEncontradoError
                  │     ├── CanalNomeDuplicadoError
                  │     ├── CanalTipoInvalidoError
                  │     ├── CanalConfiguracaoInvalidaError
                  │     ├── CanalWebhookError
                  │     └── CanalSemTelefoneError (403)
                  │
                  └── [SUB-DOMÍNIO: INTEGRAÇÃO / RUNTIME (LSP)]
                        └── CanalIntegracaoError (502 - Bad Gateway)
                              ├── CanalEntregaFalhouError
                              ├── CanalAutenticacaoFalhouError
                              ├── CanalLimiteTaxaError (429)
                              └── CanalMidiaNaoSuportadaError
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

    def __init__(self, mensagem: str, *, codigo: str | None = None, detalhe: str | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhe = detalhe #  Adicionado para capturar o erro original da API externa
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
# ESPECÍFICAS DE CANAL (AGRUPADOR)
# ══════════════════════════════════════════════════════════════════════════
class CanalException(EcoChatBotError):
    """Agrupador semântico para exceções de canal."""
    codigo = "canal_erro_generico"


# ─── SUB-DOMÍNIO: CRUD / GESTÃO (O que você já tinha) ─────────────────
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


# ─── SUB-DOMÍNIO: INTEGRAÇÃO / RUNTIME (Novo - Para LSP dos Adaptadores) ─
class CanalIntegracaoError(CanalException):
    """
    Base para falhas de comunicação com a API externa (Evolution, Telegram, etc).
    Usado pelos Adaptadores (LSP) para garantir que o BotService trate 
    todos os provedores de forma idêntica.
    """
    http_status = 502  # Bad Gateway (o provedor externo falhou)
    codigo = "canal_integracao_erro"


class CanalEntregaFalhouError(CanalIntegracaoError):
    """
    A API externa retornou erro de rede, timeout ou status >= 400.
    (De-Para: ChannelDeliveryError)
    """
    codigo = "canal_entrega_falhou"


class CanalAutenticacaoFalhouError(CanalIntegracaoError):
    """
    O token/apikey do provedor externo expirou ou é inválido (HTTP 401/403).
    (De-Para: ChannelAuthError)
    """
    http_status = 401  # Unauthorized
    codigo = "canal_autenticacao_falhou"


class CanalLimiteTaxaError(CanalIntegracaoError):
    """
    O provedor externo retornou HTTP 429 (Too Many Requests).
    (De-Para: ChannelRateLimitError)
    """
    http_status = 429
    codigo = "canal_limite_taxa_excedido"


class CanalMidiaNaoSuportadaError(CanalIntegracaoError):
    """
    O provedor externo não suporta o tipo de mídia (ex: enviar lista no PABX).
    (De-Para: ChannelUnsupportedMediaError)
    """
    http_status = 415  # Unsupported Media Type
    codigo = "canal_midia_nao_suportada"


__all__ = [
    # Base
    "EcoChatBotError",
    "RecursoNaoEncontradoError",
    "RecursoInvalidoError",
    "AcessoNegadoError",
    "LimiteCotaExcedidoError",
    # Canal (CRUD)
    "CanalException",
    "CanalNaoEncontradoError",
    "CanalNomeDuplicadoError",
    "CanalTipoInvalidoError",
    "CanalConfiguracaoInvalidaError",
    "CanalWebhookError",
    "CanalSemTelefoneError",
    # Canal (Integração/Runtime - LSP)
    "CanalIntegracaoError",
    "CanalEntregaFalhouError",
    "CanalAutenticacaoFalhouError",
    "CanalLimiteTaxaError",
    "CanalMidiaNaoSuportadaError",
]