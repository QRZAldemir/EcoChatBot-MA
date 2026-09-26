"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Departamento
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     departamento_models.py
@module   Backend / App / Models / Departamento
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa o SETOR da empresa que recebe o atendimento após o cliente
escolher uma opção no menu.

Conforme README, seção 3:
    DEPARTAMENTO = "Setor ou equipe responsável pelo atendimento"
    Exemplos: Vendas, Financeiro, Suporte, Operações

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Departamento ── (N) Atendimento

REGRAS DE NEGÓCIO
─────────────────
    • `horario_inicio` e `horario_fim` definem expediente (formato "HH:MM")
    • Fora do expediente → alerta FORA_EXPEDIENTE no painel
    • `cor` é usada na UI para identificar visualmente o departamento
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.empresa_models import Empresa


class Departamento(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Setor/equipe responsável por um tipo de atendimento."""

    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    cor: Mapped[str | None] = mapped_column(String(9))   # #RRGGBB ou #RRGGBBAA

    # ─── Expediente ───────────────────────────────────────────────────────
    horario_inicio: Mapped[str | None] = mapped_column(String(5))   # "08:00"
    horario_fim: Mapped[str | None] = mapped_column(String(5))      # "18:00"
    dias_semana: Mapped[str | None] = mapped_column(String(20))     # "1,2,3,4,5"

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="departamentos")
    atendimentos: Mapped[List["Atendimento"]] = relationship(back_populates="departamento")


__all__ = ["Departamento"]