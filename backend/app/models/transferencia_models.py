"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Histórico de Transferências
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     transferencia_models.py
@module   Backend / App / Models / Transferência
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Registro AUDITÁVEL de TODA transferência de atendimento.

O caso que motivou esta tabela:
    A cliente Xmaira entrou pelo WhatsApp, viu o menu e escolheu
    "1 — Agendamento". Foi atendida por alguém do departamento de
    Agendamento, mas ela queria Exames. O atendente transferiu.

    Sem histórico, não há como responder: "quem transferiu, de qual
    departamento para qual, e por quê?".

COMO SE USA
───────────
O destino da transferência NÃO vem do canal — vem do MENU:

    Cliente entra pelo Canal (tecnologia)
            │
            ▼
    Menu ──► MenuItem ──► Departamento ──► Atendente
                                │
                                ▼
                    (o atendente redireciona)
                                │
                                ▼
                      Transferencia (histórico)

EXEMPLO DE REGISTRO
───────────────────
    tipo                  = ATENDENTE
    departamento_origem   = 2  (Agendamento)
    departamento_destino  = 3  (Exames)
    usuario_origem        = 14 (atendente que transferiu)
    usuario_destino        = 27 (atendente que recebeu)
    motivo                = "Cliente informou que precisa de Exames, não Agendamento"

EXEMPLO PRÁTICO
───────────────
Esta é uma trilha de AUDITORIA. Um histórico que pode ser apagado não é
histórico. Por isso esta tabela NÃO herda SoftDeleteMixin — as linhas são
append-only. A retenção é prazo legal (LGPD), não remoção manual.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RELACIONAMENTO
──────────────
    Cliente     (1) ── (N) Transferencia
    Atendimento (1) ── (N) Transferencia
    Departamento (1) ── (N) Transferencia   (como origem e como destino)
    CanalContratado (1) ── (N) Transferencia
    MenuItem    (1) ── (N) Transferencia

    A Transferência é a PONTE entre o Menu (escolha do cliente) e o
    Departamento (destino). Por isso guarda `menu_item_id`: sem ele não é
    possível responder se o cliente escolheu errado ou foi mal atendido.

POR QUE NÃO TEM SOFT DELETE
──────────────────────────
    Esta é uma trilha de AUDITORIA. Um histórico que pode ser apagado não é
    histórico. Por isso esta tabela NÃO herda SoftDeleteMixin — as linhas são
    append-only. A retenção é prazo legal (LGPD), não remoção manual.

REGRAS DE NEGÓCIO
─────────────────
    • TODA transferência gera UMA linha. A ausência do registro significa
      que a transferência não aconteceu.
    • `tipo = ATENDENTE` exige `motivo` preenchido
    • `departamento_destino_id` e `usuario_destino_id` não podem ser ambos
      nulos — é preciso saber para onde o cliente foi
    • O canal é apenas contexto (`canal_contratado_id`); o destino vem
      sempre do Menu/Departamento, nunca do canal
    • `ramal_origem`/`ramal_destino` só são preenchidos em transferências
      VoIP/PABX
    • Registro imutável: sem `deleted_at`, sem update de origem/destino
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoTransferencia
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.canal_models import CanalContratado
    from app.models.menu_models import MenuItem


class Transferencia(TimestampMixin, TenantMixin, SoftDeleteMixin, Base):
    """
    Uma transferência de atendimento. Append-only.

    Não usa SoftDeleteMixin: registro de auditoria não é apagável.
    """

    __tablename__ = "transferencias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Contexto ─────────────────────────────────────────────────────────
    atendimento_id: Mapped[int] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal_contratado_id: Mapped[int | None] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="Canal por onde o cliente entrou (whatsapp, pabx, ...)",
    )
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_itens.id", ondelete="SET NULL"), nullable=True,
        comment="Opção de menu escolhida pelo cliente — quando a origem foi o menu",
    )

    # ─── De onde veio ──────────────────────────────────────────────────────
    departamento_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    usuario_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
        comment="Atendente que efetuou a transferência",
    )
    ramal_origem: Mapped[str | None] = mapped_column(
        String(20), comment="Ramal de origem — transferências VoIP"
    )

    # ─── Para onde foi ────────────────────────────────────────────────────
    departamento_destino_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    usuario_destino_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
        comment="Atendente que recebeu o atendimento",
    )
    ramal_destino: Mapped[str | None] = mapped_column(
        String(20), comment="Ramal de destino — transferências VoIP"
    )

    # ─── Classificação ────────────────────────────────────────────────────
    tipo: Mapped[TipoTransferencia] = mapped_column(
        String(20), nullable=False, default=TipoTransferencia.ATENDENTE, index=True,
        comment="menu | atendente | ramal | sistema",
    )
    motivo: Mapped[str | None] = mapped_column(
        Text, comment="Justificativa — obrigatória quando tipo = ATENDENTE"
    )

    # ─── Quando ───────────────────────────────────────────────────────────
    transferido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc), index=True,
    )

    # ─── Relacionamentos ──────────────────────────────────────────────────
    atendimento: Mapped["Atendimento"] = relationship(back_populates="transferencias")
    canal_contratado: Mapped["CanalContratado | None"] = relationship()
    menu_item: Mapped["MenuItem | None"] = relationship()


__all__ = ["Transferencia"]
