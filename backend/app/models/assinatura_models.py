"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Assinatura
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     assinatura_models.py
@module   Backend / App / Models / Assinatura
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Registro do contrato comercial entre o Cliente (tenant) e a plataforma.

⚠️ ESTE MODEL ESTÁ INCOMPLETO DE PROPOSITO
──────────────────────────────────────────
O modelo comercial de MENSAALIDADE ainda NÃO foi definido pelo negócio.
Não há regra de cálculo, não há tabela de preços, e não há vínculo entre
a assinatura e os canais contratados.

O que existe aqui é apenas a ESTRUTURA para registrar o contrato:
plano, valor base, período e situação. Quando o negócio definir como a
mensalidade é calculada a partir dos canais contratados, os campos de
valor passam a ser preenchidos.

EXEMPLO PRÁTICO
───────────────
    Cliente: Aldemir
    └── Assinatura(plano=Pro, valor_base=..., status=ATIVA)
          └── Empresa: Aldemir Ltda
                ├── Telefone 556734167800  (1 whatsapp, 1 telegram)
                └── Telefone 5567992469894 (1 whatsapp)   ← duplica a mensalidade

RELACIONAMENTO
──────────────
    Cliente (1) ── (N) Assinatura
    Empresa  (1) ── (1) Assinatura

    A assinatura pertence à Empresa, NÃO ao Telefone. O valor por canal
    contratado é derivado dos CanaisContratados da Empresa, mas essa regra
    ainda não foi implementada.

REGRAS DE NEGÓCIO
─────────────────
    • Uma Empresa tem no máximo 1 assinatura ATIVA por vez
    • `valor_base` é o valor fixo do plano — o valor por canal contratado
      NÃO é calculado aqui (regra ainda não definida)
    • Soft delete: cancelar não apaga o histórico financeiro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PlanoTenant, StatusAssinatura
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa_models import Empresa


class Assinatura(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Contrato comercial do Cliente/Empresa com a plataforma.

    ⚠️ Sem regra de cobrança. Ver o aviso no topo do arquivo.
    """

    __tablename__ = "assinaturas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Quem assina ──────────────────────────────────────────────────────

    # ─── Plano ────────────────────────────────────────────────────────────
    plano: Mapped[PlanoTenant] = mapped_column(
        String(20), nullable=False, default=PlanoTenant.BASIC,
        comment="free | basic | pro | enterprise",
    )
    status: Mapped[StatusAssinatura] = mapped_column(
        String(20), nullable=False, default=StatusAssinatura.ATIVA, index=True,
    )

    # ─── Valores (regra de cálculo ainda não definida) ─────────────────────
    valor_base: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True,
        comment="Valor fixo do plano. NÃO inclui o valor por canal.",
    )

    # ─── Vigência ─────────────────────────────────────────────────────────
    inicio_vigencia: Mapped[date | None] = mapped_column(Date, nullable=True)
    fim_vigencia: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="NULL = vigência indeterminada"
    )

    # ─── Observações ──────────────────────────────────────────────────────
    observacoes: Mapped[str | None] = mapped_column(Text)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship()


__all__ = ["Assinatura"]
