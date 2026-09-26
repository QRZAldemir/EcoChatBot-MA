"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Templates e Logs de E-mail
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     email_models.py
@module   Backend / App / Models / Email
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
    • EmailTemplate → template HTML/texto reutilizável
    • EmailLog      → cada e-mail enviado (para auditoria e tracking)

Usado para notificações transacionais (novo atendimento, resposta ao
cliente, pedido atualizado) e para campanhas por e-mail.

RELACIONAMENTO
──────────────
    Empresa       (1) ── (N) EmailTemplate
    Empresa       (1) ── (N) EmailLog
    Atendimento   (1) ── (N) EmailLog   (opcional)

REGRAS DE NEGÓCIO
─────────────────
    • `chave` única por empresa (ex.: "novo_atendimento")
    • EmailLog guarda status de abertura/clique quando rastreável
    • Corpo HTML é sanitizado antes de renderizar (XSS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusEmail
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    pass


class EmailTemplate(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Template de e-mail reutilizável."""

    __tablename__ = "email_templates"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "chave",
            name="uq_email_templates_empresa_chave",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chave: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    assunto: Mapped[str] = mapped_column(String(200), nullable=False)
    corpo_html: Mapped[str | None] = mapped_column(Text)
    corpo_texto: Mapped[str | None] = mapped_column(Text)
    variaveis: Mapped[str | None] = mapped_column(Text)   # CSV


class EmailLog(TimestampMixin, TenantMixin, Base):
    """Registro de cada e-mail enviado."""

    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_templates.id", ondelete="SET NULL")
    )
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="SET NULL"), index=True
    )

    # ─── Destinatário ─────────────────────────────────────────────────────
    destinatario: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    remetente: Mapped[str | None] = mapped_column(String(200))
    assunto: Mapped[str | None] = mapped_column(String(200))

    # ─── Estado ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusEmail.PENDENTE.value, nullable=False, index=True
    )
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aberto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Diagnóstico ──────────────────────────────────────────────────────
    erro: Mapped[str | None] = mapped_column(Text)
    message_id: Mapped[str | None] = mapped_column(String(200), index=True)


__all__ = ["EmailTemplate", "EmailLog"]