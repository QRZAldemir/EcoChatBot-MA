"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Exceptions Package
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     __init__.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: correção do import de ia_exceptions
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Barrel file do pacote `app.exceptions`. Centraliza os 9 domínios de
exceções do EcoChatBot-MA.

ESTRUTURA DO PACOTE
───────────────────
    app/exceptions/
    ├── __init__.py                    → este arquivo
    ├── base_exceptions.py             → 12 exceções base
    ├── canal_exceptions.py            → 7 exceções (canal)
    ├── auth_exceptions.py             → 12 exceções (auth)
    ├── tenant_exceptions.py           → 8 exceções (tenant)
    ├── usuario_exceptions.py          → 8 exceções (usuario)
    ├── atendimento_exceptions.py      → 7 exceções (atendimento)
    ├── ia_exceptions.py               → 10 exceções (IA + OCR + TTS)
    ├── integracao_exceptions.py       → 10 exceções (integração)
    └── webhook_exceptions.py          → 9 exceções (webhook)

TOTAL: 83 exceções em 9 arquivos + 1 barrel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ─── 1. Base ────────────────────────────────────────────────────────────
from app.exceptions.base_exceptions import (
    EcoChatBotException, ValidationException, NotFoundException,
    ConflictException, UnauthorizedException, ForbiddenException,
    ServiceException, RepositoryException, DatabaseException,
    IntegrationException, FileUploadException, EmailException,
)

# ─── 2. Canal ───────────────────────────────────────────────────────────
from app.exceptions.canal_exceptions import (
    CanalException, CanalConfiguracaoInvalidaError, CanalNaoEncontradoError,
    CanalNomeDuplicadoError, CanalTipoInvalidoError, CanalWebhookError,
)

# O projeto migrou a convenção de `*Exception` para `*Error` (ver
# app/services/canal_service.py, que é o consumidor real). Este facade ainda
# listava os nomes antigos, que nunca foram declarados em canal_exceptions.py.
# Os aliases abaixo mantêm o código legado funcionando sem quebrar a
# exportação. NÃO inventamos `CanalDesconectado*` e `CanalNaoSuportado*`:
# essas classes nunca foram escritas e seguem com funcionalidade ausente.
CanalNaoEncontradoException = CanalNaoEncontradoError
CanalJaExisteException = CanalNomeDuplicadoError
CanalWebhookException = CanalWebhookError
CanalInvalidoException = CanalTipoInvalidoError

# ─── 3. Auth ────────────────────────────────────────────────────────────
from app.exceptions.auth_exceptions import (
    AuthException, CredenciaisInvalidasException, ContaBloqueadaException,
    ContaInativaException, EmailNaoVerificadoException,
    TokenExpiradoException, TokenInvalidoException, TokenRevogadoException,
    TokenAusenteException, SessaoExpiradaException,
    PermissaoNegadaException, NivelInsuficienteException,
)

# ─── 4. Tenant ──────────────────────────────────────────────────────────
from app.exceptions.tenant_exceptions import (
    TenantException, TenantNaoEncontradoException, TenantJaExisteException,
    TenantInativoException, TenantSuspensoException, TenantAusenteException,
    TenantInvalidoException, TenantAcessoNegadoException,
)

# ─── 5. Usuário ─────────────────────────────────────────────────────────
from app.exceptions.usuario_exceptions import (
    UsuarioException, UsuarioNaoEncontradoException,
    EmailJaCadastradoException, UsernameJaCadastradoException,
    SenhaFracaException, SenhaIncorretaException,
    UsuarioInativoException, UsuarioSemDepartamentoException,
)

# ─── 6. Atendimento ─────────────────────────────────────────────────────
from app.exceptions.atendimento_exceptions import (
    AtendimentoException, AtendimentoNaoEncontradoException,
    AtendimentoJaEncerradoException, AtendimentoJaEmAndamentoException,
    AtendimentoNaoTransferivelException, AtendimentoSemAtendenteException,
    FilaCheiaException,
)

# ─── 7. IA + OCR + TTS ──────────────────────────────────────────────────
# ✅ CORREÇÃO: Alterado de 'ai_exceptions' para 'ia_exceptions'
from app.exceptions.ia_exceptions import (
    IAException, DeepSeekException, IAIndisponivelException,
    IARespostaInvalidaException, IATokenExcedidoException,
    OCRException, OCRImagemInvalidaException, OCRNenhumTextoException,
    TTSException, TTSVozNaoSuportadaException,
)

# ─── 8. Integração ──────────────────────────────────────────────────────
from app.exceptions.integracao_exceptions import (
    IntegracaoException, IntegracaoNaoConfiguradaException,
    IntegracaoDesabilitadaException, IntegracaoIndisponivelException,
    IntegracaoTimeoutException, IntegracaoRateLimitException,
    IntegracaoTokenInvalidoException, IntegracaoPayloadInvalidoException,
    IntegracaoRespostaInvalidaException, IntegracaoNaoSuportadaException,
)

# ─── 9. Webhook ─────────────────────────────────────────────────────────
from app.exceptions.webhook_exceptions import (
    WebhookException, WebhookNaoConfiguradoException,
    WebhookInvalidoException, WebhookAssinaturaInvalidaException,
    WebhookNaoAutorizadoException, WebhookDuplicadoException,
    WebhookProcessamentoException, WebhookTenantNaoIdentificadoException,
    WebhookCanalNaoIdentificadoException,
)

# ─── Exports ────────────────────────────────────────────────────────────
# ─── 10. Nomes usados pelo código que nunca foram declarados ─────────────
# Estes 7 nomes são importados por app/services/canal_service.py,
# app/services/atendimento_service.py, app/security.py e
# app/routers/atendimentos_routers.py, mas não existiam em nenhum
# *_exceptions.py — por isso 43 módulos não carregavam.
#
# NÃO foram usados alias simples: as classes existentes do mesmo domínio
# recebem `atendimento_id`/`resource` (identificador), enquanto os call sites
# passam uma mensagem completa. Um alias produziria mensagens como
# "Contexto não encontrado. não encontrado". Por isso cada uma é uma
# subclasse que aceita `message`.
#
# Nenhum código de status novo foi inventado: cada subclasse replica o da
# classe equivalente que já existia (indicado no docstring).


class NegocioException(ValidationException):
    """Regra de negócio violada. HTTP 422 (de ValidationException)."""

    def __init__(self, message='Regra de negócio violada', detail=None, fields=None):
        super().__init__(message=message, detail=detail, fields=fields)
        self.error_code = 'NEGOCIO_ERROR'


class ValidacaoNegocioException(NegocioException):
    """Validação de regra de negócio. HTTP 422 (de NegocioException)."""

    def __init__(self, message='Regra de negócio inválida', detail=None, fields=None):
        super().__init__(message=message, detail=detail, fields=fields)
        self.error_code = 'VALIDACAO_NEGOCIO_ERROR'


class RecursoInvalidoError(NegocioException):
    """
    Recurso inválido (ex.: departamento inexistente, configuração malformada).
    HTTP 422 (de NegocioException).
    """

    def __init__(self, message='Recurso inválido', detail=None, fields=None):
        super().__init__(message=message, detail=detail, fields=fields)
        self.error_code = 'RECURSO_INVALIDO_ERROR'


class RecursoNaoEncontradoException(EcoChatBotException):
    """Recurso não encontrado. HTTP 404 (mesmo código de NotFoundException)."""

    def __init__(self, message='Recurso não encontrado', detail=None):
        super().__init__(
            message=message,
            status_code=404,
            detail=detail,
            error_code='NOT_FOUND',
        )


class AtendimentoFinalizadoError(AtendimentoException):
    """
    Atendimento já finalizado. HTTP 409 (mesmo código de
    AtendimentoJaEncerradoException). Nome distinto porque os call sites o
    tratam como "finalizado", não "encerrado".
    """

    def __init__(self, message='Atendimento já finalizado', detail=None):
        super().__init__(
            message=message,
            status_code=409,
            detail=detail,
            error_code='ATENDIMENTO_FINALIZADO_ERROR',
        )


class AtendimentoNaoEncontradoError(AtendimentoException):
    """Atendimento não encontrado. HTTP 404 (de AtendimentoNaoEncontradoException)."""

    def __init__(self, message='Atendimento não encontrado', detail=None):
        super().__init__(
            message=message,
            status_code=404,
            detail=detail,
            error_code='ATENDIMENTO_NAO_ENCONTRADO_ERROR',
        )


# Único caso em que o alias é seguro: o call site é `raise NaoAutenticadoException()`
# sem argumentos, e UnauthorizedException já tem message padrão.
NaoAutenticadoException = UnauthorizedException


__all__ = [
    # Base (12)
    'EcoChatBotException', 'ValidationException', 'NotFoundException',
    'ConflictException', 'UnauthorizedException', 'ForbiddenException',
    'ServiceException', 'RepositoryException', 'DatabaseException',
    'IntegrationException', 'FileUploadException', 'EmailException',
    # Canal — *Error é a convenção vigente; *Exception são aliases legados
    'CanalException', 'CanalConfiguracaoInvalidaError', 'CanalNaoEncontradoError',
    'CanalNomeDuplicadoError', 'CanalTipoInvalidoError', 'CanalWebhookError',
    'CanalNaoEncontradoException', 'CanalJaExisteException',
    'CanalInvalidoException', 'CanalWebhookException',
    # Auth (12)
    'AuthException', 'CredenciaisInvalidasException', 'ContaBloqueadaException',
    'ContaInativaException', 'EmailNaoVerificadoException',
    'TokenExpiradoException', 'TokenInvalidoException', 'TokenRevogadoException',
    'TokenAusenteException', 'SessaoExpiradaException',
    'PermissaoNegadaException', 'NivelInsuficienteException',
    # Tenant (8)
    'TenantException', 'TenantNaoEncontradoException', 'TenantJaExisteException',
    'TenantInativoException', 'TenantSuspensoException', 'TenantAusenteException',
    'TenantInvalidoException', 'TenantAcessoNegadoException',
    # Usuário (8)
    'UsuarioException', 'UsuarioNaoEncontradoException',
    'EmailJaCadastradoException', 'UsernameJaCadastradoException',
    'SenhaFracaException', 'SenhaIncorretaException',
    'UsuarioInativoException', 'UsuarioSemDepartamentoException',
    # Atendimento (7)
    'AtendimentoException', 'AtendimentoNaoEncontradoException',
    'AtendimentoJaEncerradoException', 'AtendimentoJaEmAndamentoException',
    'AtendimentoNaoTransferivelException', 'AtendimentoSemAtendenteException',
    'FilaCheiaException',
    # IA + OCR + TTS (10)
    'IAException', 'DeepSeekException', 'IAIndisponivelException',
    'IARespostaInvalidaException', 'IATokenExcedidoException',
    'OCRException', 'OCRImagemInvalidaException', 'OCRNenhumTextoException',
    'TTSException', 'TTSVozNaoSuportadaException',
    # Integração (10)
    'IntegracaoException', 'IntegracaoNaoConfiguradaException',
    'IntegracaoDesabilitadaException', 'IntegracaoIndisponivelException',
    'IntegracaoTimeoutException', 'IntegracaoRateLimitException',
    'IntegracaoTokenInvalidoException', 'IntegracaoPayloadInvalidoException',
    'IntegracaoRespostaInvalidaException', 'IntegracaoNaoSuportadaException',
    # Webhook (9)
    'WebhookException', 'WebhookNaoConfiguradoException',
    'WebhookInvalidoException', 'WebhookAssinaturaInvalidaException',
    'WebhookNaoAutorizadoException', 'WebhookDuplicadoException',
    'WebhookProcessamentoException', 'WebhookTenantNaoIdentificadoException',
    'WebhookCanalNaoIdentificadoException',
    # Nomes usados pelo código que nunca foram declarados (seção 10)
    'NegocioException', 'ValidacaoNegocioException', 'RecursoInvalidoError',
    'RecursoNaoEncontradoException', 'AtendimentoFinalizadoError',
    'AtendimentoNaoEncontradoError', 'NaoAutenticadoException',
]