"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Campanha de Marketing
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     campanha_models.py
@module   Backend / App / Models / Campanha
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Disparo em massa de mensagens para uma lista de contatos, em um ou mais
canais contratados. Usada para promoções, avisos, cobranças e lembretes.

EXEMPLO PRÁTICO
───────────────
    Campanha(
        nome="Black Friday 2026",
        canal_contratado_id=<WhatsApp>,
        modelo_mensagem_chave="promo_black_friday",
        agendada_para="2026-11-27 09:00",
        publico_tag="cliente_vip",
    )

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Campanha
    CanalContratado (1) ── (N) Campanha
    Cliente (tenant raiz) ── (N) Campanha

REGRAS DE NEGÓCIO
─────────────────
    • Só dispara em canais ATIVOS e CONTRATADOS
    • Respeita opt-out do contato (LGPD)
    • `publico_tag` filtra contatos por tag
    • Progresso: enviados / total
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusCampanha
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_contratado_models import CanalContratado
    from app.models.cliente_models import Cliente


class Campanha(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Disparo em massa de mensagens."""

    __tablename__ = "campanhas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)

    # ─── Conteúdo ─────────────────────────────────────────────────────────
    modelo_mensagem_chave: Mapped[str | None] = mapped_column(String(80))
    conteudo_override: Mapped[str | None] = mapped_column(Text)
    # se preenchido, ignora o modelo e usa este texto

    # ─── Público-alvo ─────────────────────────────────────────────────────
    publico_tag: Mapped[str | None] = mapped_column(String(120))
    publico_consulta: Mapped[str | None] = mapped_column(Text)
    # SQL/filtro avançado (validado antes de usar)

    # ─── Agendamento ──────────────────────────────────────────────────────
    agendada_para: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Progresso ────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusCampanha.RASCUNHO.value, nullable=False, index=True
    )
    total_destinatarios: Mapped[int] = mapped_column(Integer, default=0)
    enviados: Mapped[int] = mapped_column(Integer, default=0)
    falhas: Mapped[int] = mapped_column(Integer, default=0)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship(back_populates="campanhas")
    canal_contratado: Mapped["CanalContratado"] = relationship()


__all__ = ["Campanha"]