"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Contato
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     contato_models.py
@module   Backend / App / Models / Contato
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa a PESSOA (física ou jurídica) que conversa com o sistema,
independente do canal de mensageria.

Um mesmo Contato pode existir em vários canais (WhatsApp + Telegram +
PABX) — por isso a unicidade é (cliente_id, canal_tipo, canal_identificador)
e NÃO apenas o telefone.

RELACIONAMENTO
──────────────
    Cliente (1) ── (N) Contato ── (N) Atendimento

REGRAS DE NEGÓCIO
─────────────────
    • Não apagar contatos — apenas soft delete (LGPD: direito ao esquecimento
      é tratado por rotina de anonimização, não por DELETE)
    • `canal_identificador` é o telefone/chat_id/handle
    • `tags` é CSV simples (separado por vírgula) — simplificação inicial;
      futuramente vira tabela `tags` + `contato_tags`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.cliente_models import Cliente


class Contato(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Pessoa que interage com o sistema em qualquer canal."""

    __tablename__ = "contatos"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id", "canal_tipo", "canal_identificador",
            name="uq_contatos_cliente_canal",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str | None] = mapped_column(String(150), index=True)
    apelido: Mapped[str | None] = mapped_column(String(80))

    # ─── Chave no canal ───────────────────────────────────────────────────
    canal_tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    canal_identificador: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    # ─── Contato tradicional ──────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(20))

    # ─── Metadados ────────────────────────────────────────────────────────
    tags: Mapped[str | None] = mapped_column(Text)   # CSV simples
    notas: Mapped[str | None] = mapped_column(Text)
    ultima_interacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Relacionamentos ──────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship(back_populates="contatos")
    atendimentos: Mapped[List["Atendimento"]] = relationship(
        back_populates="contato", cascade="all, delete-orphan"
    )


__all__ = ["Contato"]