"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Atendimento
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_models.py
@module   Backend / App / Models / Atendimento
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa UMA conversa em andamento entre o cliente e a empresa. É o
coração do sistema — o registro que aparece no painel do atendente.

FLUXO (README, seção 2)
───────────────────────
    1. Cliente envia mensagem
    2. Sistema apresenta menu
    3. Cliente escolhe opção → cria Atendimento com:
         • canal_contratado (WhatsApp, Telegram...)
         • menu_item escolhido
         • departamento destino
    4. Roteiro é carregado → respostas vão em AtendimentoContexto
    5. Atendente designado → status EM_ANDAMENTO
    6. Atendente finaliza → status FINALIZADO

RELACIONAMENTO
──────────────
    Atendimento (N) ── (1) Contato
                    ├── (1) Empresa
                    ├── (1) CanalContratado
                    ├── (1) MenuItem
                    ├── (1) Departamento
                    ├── (1) Usuario (atendente)
                    ├── (N) AtendimentoContexto
                    └── (N) ChamadaPABX

REGRAS DE NEGÓCIO
─────────────────
    • `protocolo` é único globalmente (ex.: "2026-0001234")
    • `finalizado_em` preenchido quando status FINALIZADO
    • Alertas do painel (README seção 10) derivam deste modelo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    OrigemAtendimento,
    PrioridadeAtendimento,
    StatusAtendimento,
)
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_context_models import AtendimentoContexto
    from app.models.canal_contratado_models import CanalContratado
    from app.models.chamada_pabx_models import ChamadaPABX
    from app.models.contato_models import Contato
    from app.models.departamento_models import Departamento
    from app.models.empresa_models import Empresa, Usuario
    from app.models.menu_models import MenuItem


class Atendimento(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Conversa entre cliente e empresa em um canal contratado."""

    __tablename__ = "atendimentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── FKs de contexto ──────────────────────────────────────────────────
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contato_id: Mapped[int] = mapped_column(
        ForeignKey("contatos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_itens.id", ondelete="SET NULL"), index=True
    )
    departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL"), index=True
    )
    atendente_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    protocolo: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    assunto: Mapped[str | None] = mapped_column(String(200))

    # ─── Estado ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusAtendimento.AGUARDANDO.value,
        nullable=False, index=True,
    )
    prioridade: Mapped[str] = mapped_column(
        String(20), default=PrioridadeAtendimento.NORMAL.value, nullable=False
    )
    origem: Mapped[str] = mapped_column(
        String(20), default=OrigemAtendimento.BOT.value, nullable=False
    )

    # ─── Tempos ───────────────────────────────────────────────────────────
    iniciado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    primeira_resposta_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    # ─── Conteúdo ─────────────────────────────────────────────────────────
    resumo: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)   # CSV

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship()
    contato: Mapped["Contato"] = relationship(back_populates="atendimentos")
    canal_contratado: Mapped["CanalContratado"] = relationship(
        back_populates="atendimentos"
    )
    menu_item: Mapped["MenuItem | None"] = relationship()
    departamento: Mapped["Departamento | None"] = relationship(
        back_populates="atendimentos"
    )
    atendente: Mapped["Usuario | None"] = relationship()

    contextos: Mapped[List["AtendimentoContexto"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan"
    )
    chamadas: Mapped[List["ChamadaPABX"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan"
    )


__all__ = ["Atendimento"]