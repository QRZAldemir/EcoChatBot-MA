"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Tenant Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     tenant_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "TENANT" (multi-tenant) do
EcoChatBot-Marcx.

Todas as classes herdam de `TenantException`, que por sua vez herda de
`EcoChatBotException`, garantindo:

    • status_code HTTP
    • error_code programático
    • detail para resposta JSON
    • método to_dict() para serialização

DOMÍNIO "TENANT"
───────────────
O EcoChatBot-Marcx é MULTI-TENANT (SaaS). Cada "tenant" é uma EMPRESA
cliente que usa o sistema com dados isolados.

Conceitos:
    • Tenant (Empresa)    → cliente que contratou o SaaS
    • User (Usuário)      → pertence a 1 empresa
    • Isolamento          → dados de 1 empresa NÃO vê os de outra
    • Identificação       → via JWT (`empresa_id`) ou header `X-Tenant-Id`
    • Domínio/subdomínio  → ex.: `clinica-x.ecochat.marcx.com.br`

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────┬─────────┬─────────────────────┐
    │ Classe                               │ Status  │ Quando usar         │
    ├──────────────────────────────────────┼─────────┼─────────────────────┤
    │ TenantException                      │ 500     │ Base                │
    │ TenantNaoEncontradoException         │ 404     │ Tenant não existe   │
    │ TenantInativoException               │ 403     │ Tenant desativado   │
    │ TenantSuspensoException              │ 402     │ Pagamento pendente  │
    │ TenantJaExisteException              │ 409     │ Tenant duplicado    │
    │ TenantInvalidoException              │ 422     │ Tenant inválido     │
    │ TenantAusenteException               │ 400     │ Sem tenant no req.  │
    │ TenantAcessoNegadoException          │ 403     │ Cross-tenant        │
    └──────────────────────────────────────┴─────────┴─────────────────────┘

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções servem a QUALQUER canal (WhatsApp, Telegram, Discord,
Facebook, Instagram, PABX) e a QUALQUER segmento de negócio.

USO
───
    from app.exceptions import TenantNaoEncontradoException

    if not tenant:
        raise TenantNaoEncontradoException(empresa_id=42)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "TENANT"
# ═══════════════════════════════════════════════════════════════════════════


class TenantException(EcoChatBotException):
    """
    Classe BASE para todas as exceções do domínio "tenant".

    Herda de `EcoChatBotException` (default status_code=500).
    """

    def __init__(
        self,
        message: str = 'Erro relacionado ao tenant',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'TENANT_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE EXISTÊNCIA
# ═══════════════════════════════════════════════════════════════════════════


class TenantNaoEncontradoException(TenantException):
    """
    TENANT NÃO ENCONTRADO no sistema.

    HTTP Status: 404 Not Found

    Exemplo:
        raise TenantNaoEncontradoException(empresa_id=42)
    """

    def __init__(self, empresa_id: Optional[int] = None) -> None:
        message = 'Tenant (empresa) não encontrado'
        if empresa_id:
            message += f': {empresa_id}'

        super().__init__(
            message=message,
            status_code=404,
            error_code='TENANT_NAO_ENCONTRADO',
        )


class TenantJaExisteException(TenantException):
    """
    TENANT JÁ EXISTE (CNPJ ou slug duplicado).

    HTTP Status: 409 Conflict

    Exemplo:
        raise TenantJaExisteException(cnpj='12.345.678/0001-90')
    """

    def __init__(self, cnpj: Optional[str] = None, slug: Optional[str] = None) -> None:
        message = 'Já existe um tenant com estes dados'
        if cnpj:
            message += f' (CNPJ: {cnpj})'
        if slug:
            message += f' (slug: {slug})'

        super().__init__(
            message=message,
            status_code=409,
            error_code='TENANT_JA_EXISTE',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE ESTADO
# ═══════════════════════════════════════════════════════════════════════════


class TenantInativoException(TenantException):
    """
    TENANT INATIVO (desativado manualmente ou nunca ativado).

    HTTP Status: 403 Forbidden

    Exemplo:
        raise TenantInativoException(empresa_id=42)
    """

    def __init__(self, empresa_id: Optional[int] = None) -> None:
        message = 'Tenant está inativo'
        if empresa_id:
            message += f': {empresa_id}'

        super().__init__(
            message=message,
            status_code=403,
            error_code='TENANT_INATIVO',
        )


class TenantSuspensoException(TenantException):
    """
    TENANT SUSPENSO por inadimplência / pagamento pendente.

    HTTP Status: 402 Payment Required

    Exemplo:
        raise TenantSuspensoException(empresa_id=42, motivo='pagamento')
    """

    def __init__(
        self,
        empresa_id: Optional[int] = None,
        motivo: Optional[str] = None,
    ) -> None:
        message = 'Tenant suspenso'
        if empresa_id:
            message += f': {empresa_id}'
        if motivo:
            message += f'. Motivo: {motivo}'

        super().__init__(
            message=message,
            status_code=402,
            error_code='TENANT_SUSPENSO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE REQUISIÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class TenantAusenteException(TenantException):
    """
    TENANT AUSENTE na requisição (sem `empresa_id` no JWT ou header).

    HTTP Status: 400 Bad Request

    Exemplo:
        raise TenantAusenteException()
    """

    def __init__(self) -> None:
        super().__init__(
            message='Tenant não identificado na requisição. Envie X-Tenant-Id ou faça login.',
            status_code=400,
            error_code='TENANT_AUSENTE',
        )


class TenantInvalidoException(TenantException):
    """
    TENANT INVÁLIDO (formato errado, campos faltando).

    HTTP Status: 422 Unprocessable Entity

    Exemplo:
        raise TenantInvalidoException('CNPJ inválido')
    """

    def __init__(self, message: str = 'Dados do tenant inválidos') -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code='TENANT_INVALIDO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE ISOLAMENTO (CROSS-TENANT)
# ═══════════════════════════════════════════════════════════════════════════


class TenantAcessoNegadoException(TenantException):
    """
    ACESSO NEGADO entre tenants (tentativa de CROSS-TENANT).

    HTTP Status: 403 Forbidden

    ⚠️ SEGURANÇA: usuário de 1 tenant tentou acessar dados de outro.
    Este é um evento de SEGURANÇA que deve ser LOGADO.

    Exemplo:
        raise TenantAcessoNegadoException(
            tenant_user=42,
            tenant_recurso=99,
        )
    """

    def __init__(
        self,
        tenant_user: Optional[int] = None,
        tenant_recurso: Optional[int] = None,
    ) -> None:
        message = 'Acesso negado: recurso pertence a outro tenant'
        if tenant_user and tenant_recurso:
            message += f' (seu tenant: {tenant_user}, tenant do recurso: {tenant_recurso})'

        super().__init__(
            message=message,
            status_code=403,
            error_code='TENANT_ACESSO_NEGADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'TenantException',
    'TenantNaoEncontradoException',
    'TenantJaExisteException',
    'TenantInativoException',
    'TenantSuspensoException',
    'TenantAusenteException',
    'TenantInvalidoException',
    'TenantAcessoNegadoException',
]