"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Exceptions Package
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
exceções do EcoChatBot-Marcx.

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
    CanalException, CanalNaoEncontradoException, CanalJaExisteException,
    CanalInvalidoException, CanalDesconectadoException,
    CanalNaoSuportadoException, CanalWebhookException,
)

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
__all__ = [
    # Base (12)
    'EcoChatBotException', 'ValidationException', 'NotFoundException',
    'ConflictException', 'UnauthorizedException', 'ForbiddenException',
    'ServiceException', 'RepositoryException', 'DatabaseException',
    'IntegrationException', 'FileUploadException', 'EmailException',
    # Canal (7)
    'CanalException', 'CanalNaoEncontradoException', 'CanalJaExisteException',
    'CanalInvalidoException', 'CanalDesconectadoException',
    'CanalNaoSuportadoException', 'CanalWebhookException',
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
]