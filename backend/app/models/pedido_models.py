"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Pedido
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     pedido_models.py
@module   Backend / App / Models / Pedido
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa um PEDIDO originado dentro de um atendimento — usado quando
a empresa é de comércio/e-commerce e o roteiro inclui itens.

O pedido referencia o Atendimento de origem (rastreabilidade total):
    Atendimento #1234 → Pedido #5501 → Itens

RELACIONAMENTO
──────────────
    Cliente    (1) ── (N) Pedido
    Atendimento (1) ── (N) Pedido
    Contato    (1) ── (N) Pedido
    Pedido     (1) ── (N) PedidoItem

REGRAS DE NEGÓCIO
─────────────────
    • `numero` único por Empresa (ex.: "2026-00001")
    • Total calculado em serviço, não no ORM
    • Status segue `StatusPedido`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusPedido
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.cliente_models import Cliente


class Pedido(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Pedido feito dentro de um atendimento."""

    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="SET NULL"), index=True
    )
    contato_id: Mapped[int | None] = mapped_column(
        ForeignKey("contatos.id", ondelete="SET NULL"), index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    numero: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    observacoes: Mapped[str | None] = mapped_column(Text)

    # ─── Valores ──────────────────────────────────────────────────────────
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    desconto: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    frete: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # ─── Estado ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusPedido.CRIADO.value, nullable=False, index=True
    )

    # ─── Relacionamentos ──────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship(back_populates="pedidos")
    itens: Mapped[List["PedidoItem"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )


class PedidoItem(TimestampMixin, Base):
    """Item individual de um pedido."""

    __tablename__ = "pedido_itens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(80))
    quantidade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_unitario: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")


__all__ = ["Pedido", "PedidoItem"]