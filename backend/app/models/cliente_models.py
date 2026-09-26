"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Cliente (Tenant Raiz)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     cliente_models.py
@module   Backend / App / Models / Cliente
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa o TENANT RAIZ da plataforma. É o nível mais alto de
isolamento: um Cliente agrupa N Empresas, N Contatos, N Canais etc.

Este modelo está alinhado ao roadmap declarado no README (seção 11):
"Implementar suporte a Multi-Empresa ou Multi-Tenant". Mesmo que hoje
só exista 1 Cliente por instalação, o modelo já nasce pronto para
múltiplos.

RELACIONAMENTO
──────────────
    Cliente (1) ──── (N) Empresa
                ├─── (N) Contato
                ├─── (N) CanalMensageria
                ├─── (N) Campanha
                ├─── (N) Pedido
                └─── (N) Atendimento (via TenantMixin)

REGRAS DE NEGÓCIO
─────────────────
    • `slug` é único globalmente (URL-safe)
    • `cnpj` é único quando informado
    • Soft delete: cancelar plano NÃO apaga dados
    • `limite_*` é validado em serviço, não no ORM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PlanoTenant, StatusTenant
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.campanha_models import Campanha
    from app.models.canal_models import CanalMensageria
    from app.models.contato_models import Contato
    from app.models.empresa_models import Empresa
    from app.models.pedido_models import Pedido


class Cliente(TimestampMixin, SoftDeleteMixin, Base):
    """Tenant raiz da plataforma."""

    __tablename__ = "clientes"

    # ─── Chave primária ───────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Identificação legal ──────────────────────────────────────────────
    razao_social: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nome_fantasia: Mapped[str | None] = mapped_column(String(200))
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)

    # ─── Contato principal ────────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(20))

    # ─── Comercial ────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusTenant.ATIVO.value, nullable=False, index=True
    )
    plano: Mapped[str] = mapped_column(
        String(20), default=PlanoTenant.FREE.value, nullable=False
    )
    limite_empresas: Mapped[int] = mapped_column(default=1, nullable=False)
    limite_usuarios: Mapped[int] = mapped_column(default=5, nullable=False)
    limite_canais: Mapped[int] = mapped_column(default=2, nullable=False)

    # ─── Diversos ─────────────────────────────────────────────────────────
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresas: Mapped[List["Empresa"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contatos: Mapped[List["Contato"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    canais_mensageria: Mapped[List["CanalMensageria"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    campanhas: Mapped[List["Campanha"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    pedidos: Mapped[List["Pedido"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )


__all__ = ["Cliente"]