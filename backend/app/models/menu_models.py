"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Menu e MenuItem
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     menu_models.py
@module   Backend / App / Models / Menu
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define o MENU apresentado ao cliente quando ele entra em contato, e cada
ITEM desse menu (opção escolhida).

    Menu        → cabeçalho ("Menu Principal", saudação, canal vinculado)
    MenuItem    → cada opção ("1. Atendimento", "2. Agendamento"...)

Cada MenuItem aponta para um DEPARTAMENTO (quem atende) e, opcionalmente,
para um ROTEIRO (qual HTML carregar depois da escolha).

EXEMPLO PRÁTICO
───────────────
    Menu: "Principal" (vinculado ao CanalContratado WhatsApp)
    ├── Item 1: "Atendimento ao Cliente"   → Depto: Suporte    → Roteiro: suporte.html
    ├── Item 2: "Agendamento Ambulatorial" → Depto: Ambulat.   → Roteiro: agendamento.html
    ├── Item 3: "Financeiro"               → Depto: Financeiro → Roteiro: financeiro.html
    └── Item 4: "Falar com Atendente"      → Depto: Suporte    → (sem roteiro)

RELACIONAMENTO
──────────────
    CanalContratado (1) ── (N) Menu ── (N) MenuItem
                                          │
                                          ├── Departamento (N:1)
                                          └── Roteiro      (N:1, opcional)

REGRAS DE NEGÓCIO
─────────────────
    • Se o Menu não tem canal vinculado, é o menu DEFAULT da Empresa
    • `ordem` define a sequência de exibição (1, 2, 3...)
    • MenuItem pode existir sem Roteiro → significa "transferir direto
      para humano"
    • Emojis no título são permitidos (ex.: "🍔 Fazer Pedido")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_models import CanalContratado
    from app.models.departamento_models import Departamento
    from app.models.roteiro_models import Roteiro


class Menu(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Menu apresentado ao cliente ao iniciar contato.

    Pode ser único por Empresa (menu default) ou específico por canal
    contratado — útil quando WhatsApp e Telegram têm apresentações
    diferentes.
    """

    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    canal_contratado_id: Mapped[int | None] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="CASCADE"), index=True
    )

    # ─── Apresentação ─────────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    saudacao: Mapped[str | None] = mapped_column(Text)
    # ex.: "Olá! 👋 Sou o assistente da Aldemir Ltda. Escolha uma opção:"
    rodape: Mapped[str | None] = mapped_column(Text)
    # ex.: "Digite *voltar* a qualquer momento."

    # ─── Comportamento ────────────────────────────────────────────────────
    tempo_espera_seg: Mapped[int] = mapped_column(Integer, default=300)   # 5min
    tentativas_max: Mapped[int] = mapped_column(Integer, default=3)
    fallback_departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL")
    )

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    canal_contratado: Mapped["CanalContratado | None"] = relationship(back_populates="menus")
    itens: Mapped[List["MenuItem"]] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        order_by="MenuItem.ordem",
    )


class MenuItem(TimestampMixin, SoftDeleteMixin, Base):
    """
    Opção individual do menu.

    Aponta para um Departamento (quem atende) e, opcionalmente, um
    Roteiro (qual HTML carregar). Se não houver roteiro, transfere
    direto para atendimento humano.
    """

    __tablename__ = "menu_itens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_id: Mapped[int] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True
    )
    departamento_id: Mapped[int] = mapped_column(
        ForeignKey("departamentos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    roteiro_id: Mapped[int | None] = mapped_column(
        ForeignKey("roteiros.id", ondelete="SET NULL")
    )

    # ─── Apresentação ─────────────────────────────────────────────────────
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    # ex.: "1. Agendamento Ambulatorial"
    descricao: Mapped[str | None] = mapped_column(Text)

    # ─── Comportamento especial ───────────────────────────────────────────
    atalho: Mapped[str | None] = mapped_column(String(20))
    # ex.: "1", "AG" — tecla/atalho que seleciona este item
    transfere_direto: Mapped[bool] = mapped_column(Boolean, default=False)
    # True → pula roteiro, vai direto para atendente

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    menu: Mapped["Menu"] = relationship(back_populates="itens")
    departamento: Mapped["Departamento"] = relationship()
    roteiro: Mapped["Roteiro | None"] = relationship()


__all__ = ["Menu", "MenuItem"]