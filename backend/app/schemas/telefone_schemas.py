"""
================================================================================
MÓDULO: app/schemas/telefone_schemas.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 1.0.0
OBJETIVO: Define os schemas Pydantic para o Telefone da Empresa, que é o eixo
          da contratação de canais. Valida e normaliza o número em E.164.
PASTA: backend/app/schemas/
================================================================================

REGRA DE NEGÓCIO
----------------
    Cada telefone comporta 1 canal de cada tipo (`UNIQUE (telefone_id, tipo)`
    em `canais_contratados`). O mesmo telefone PODE atender canais de tipos
    diferentes. Com um 2º telefone, a Empresa PODE contratar um 2º WhatsApp.

Ver `docs/ESTUDO_DE_CASO_CONTRATO_DE_CANAIS.md`.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================
# SCHEMAS BASE
# ============================================

class TelefoneBase(BaseModel):
    """Dados de um telefone da Empresa."""

    numero: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Número em E.164, apenas dígitos — ex.: 556734167800",
    )
    pais: str = Field(
        "55", min_length=1, max_length=4,
        description="Código do país ISO — 55 = Brasil",
    )
    descricao: Optional[str] = Field(
        None, max_length=80,
        description='Identificação do número — ex.: "Principal", "Loja Centro"',
    )
    principal: bool = Field(
        False, description="Marca o telefone principal da Empresa"
    )
    ativo: bool = Field(True, description="Soft delete: desativar preserva o histórico")

    @field_validator("numero")
    @classmethod
    def validar_numero(cls, v: str) -> str:
        """Aceita apenas dígitos, no formato E.164 (10 a 15 dígitos)."""
        apenas_digitos = "".join(filter(str.isdigit, v))
        if not 10 <= len(apenas_digitos) <= 15:
            raise ValueError(
                "Telefone deve ter entre 10 e 15 dígitos (E.164). "
                f"Recebido: {v!r}"
            )
        return apenas_digitos

    @field_validator("pais")
    @classmethod
    def validar_pais(cls, v: str) -> str:
        return "".join(filter(str.isdigit, v)) or "55"


# ============================================
# SCHEMAS DE CRIAÇÃO / ATUALIZAÇÃO
# ============================================

class TelefoneCreate(TelefoneBase):
    """Cadastro de um novo telefone da Empresa."""


class TelefoneUpdate(BaseModel):
    """Atualização parcial. `numero` e `pais` não são alteráveis."""

    descricao: Optional[str] = Field(None, max_length=80)
    principal: Optional[bool] = None
    ativo: Optional[bool] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class TelefoneResponse(TelefoneBase):
    """Telefone retornado pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    deletado_em: Optional[datetime] = Field(
        None, validation_alias="deleted_at",
        description="Preenchido quando o telefone é desativado (soft delete)",
    )


class TelefoneComCanais(TelefoneResponse):
    """Telefone com os canais contratados nele."""

    canais: list[dict] = Field(
        default_factory=list,
        description="Canais contratados neste telefone — 1 por tipo",
    )


__all__ = [
    "TelefoneBase",
    "TelefoneCreate",
    "TelefoneUpdate",
    "TelefoneResponse",
    "TelefoneComCanais",
]
