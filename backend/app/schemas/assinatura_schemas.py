"""
================================================================================
MÓDULO: app/schemas/assinatura_schemas.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 1.0.0
OBJETIVO: Define os schemas Pydantic do contrato comercial (assinatura).
          ⚠️ SEM REGRA DE COBRANÇA — o modelo de mensalidade não foi definido.
PASTA: backend/app/schemas/
================================================================================

⚠️ O MODELO COMERCIAL DE MENSAALIDADE AINDA NÃO FOI DEFINIDO.
Estes schemas expõem apenas a ESTRUTURA do contrato (plano, valor base,
vigência, situação). Não há cálculo de valor por canal contratado.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal

from app.models.enums import PlanoTenant, StatusAssinatura


# ============================================
# SCHEMAS BASE
# ============================================


# No Pydantic 2.7 `max_digits`/`decimal_places` não são mais constraints de
# `Field()` ( Were V1). `condecimal` é a API equivalente, e os mesmos limites
# já estão no model: `Numeric(12, 2)`.
ValorMonetario = condecimal(max_digits=12, decimal_places=2, ge=0)


class AssinaturaBase(BaseModel):
    """Contrato comercial da Empresa."""

    plano: PlanoTenant = Field(
        PlanoTenant.BASIC, description="free | basic | pro | enterprise"
    )
    status: StatusAssinatura = Field(
        StatusAssinatura.ATIVA,
        description="trial | ativa | inadimplente | suspensa | cancelada",
    )
    valor_base: Optional[ValorMonetario] = Field(
        None,
        description="Valor fixo do plano. NÃO inclui o valor por canal — "
                    "essa regra ainda não foi definida.",
    )
    inicio_vigencia: Optional[date] = None
    fim_vigencia: Optional[date] = Field(
        None, description="NULL = vigência indeterminada"
    )
    observacoes: Optional[str] = None


# ============================================
# SCHEMAS DE CRIAÇÃO / ATUALIZAÇÃO
# ============================================

class AssinaturaCreate(AssinaturaBase):
    """Nova assinatura para uma Empresa."""


class AssinaturaUpdate(BaseModel):
    """Atualização parcial do contrato."""

    plano: Optional[PlanoTenant] = None
    status: Optional[StatusAssinatura] = None
    valor_base: Optional[ValorMonetario] = None
    inicio_vigencia: Optional[date] = None
    fim_vigencia: Optional[date] = None
    observacoes: Optional[str] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class AssinaturaResponse(AssinaturaBase):
    """Assinatura retornada pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None


__all__ = [
    "AssinaturaBase",
    "AssinaturaCreate",
    "AssinaturaUpdate",
    "AssinaturaResponse",
]
