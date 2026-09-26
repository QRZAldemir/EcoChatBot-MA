"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Chamada PABX (VoIP)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     chamada_pabx_models.py
@module   Backend / App / Models / Chamada PABX
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Registra cada CHAMADA TELEFÔNICA VoIP (ramal → ramal, DID → ramal,
cliente → 0800) quando a Empresa contrata o canal PABX.

Conforme sua explicação: se a Empresa contratar PABX, ela pode receber
e originar ligações direto pelo EcoChatBot-MA (via Asterisk/FreeSWITCH/
MicroSIP). Cada ligação vira um registro aqui.

RELACIONAMENTO
──────────────
    Atendimento (1) ── (N) ChamadaPABX
    CanalContratado (1) ── (N) ChamadaPABX

    Uma mesma conversa pode ter várias chamadas (reconexões, transferências).

REGRAS DE NEGÓCIO
─────────────────
    • `call_id` é o identificador único da operadora (SIP Call-ID)
    • `duracao_seg` é calculada em `finalizado_em - atendida_em`
    • Gravação fica no storage externo — só guardamos o path/URL
    • LGPD: gravação é opcional e precisa de consentimento
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusChamada, TipoChamada
from app.models.mixins import TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.canal_contratado_models import CanalContratado


class ChamadaPABX(TimestampMixin, TenantMixin, Base):
    """Registro de uma chamada VoIP (entrada, saída ou interna)."""

    __tablename__ = "chamadas_pabx"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="SET NULL"), index=True
    )
    canal_contratado_id: Mapped[int | None] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="SET NULL"), index=True
    )

    # ─── Identificação SIP/Asterisk ───────────────────────────────────────
    call_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    ramal_origem: Mapped[str | None] = mapped_column(String(20))
    ramal_destino: Mapped[str | None] = mapped_column(String(20))
    numero_externo: Mapped[str | None] = mapped_column(String(20), index=True)
    # número do cliente (fora da empresa)

    # ─── Estado ───────────────────────────────────────────────────────────
    tipo: Mapped[str] = mapped_column(
        String(20), default=TipoChamada.ENTRADA.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=StatusChamada.INICIADA.value, nullable=False, index=True
    )

    # ─── Tempos ───────────────────────────────────────────────────────────
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    atendida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracao_seg: Mapped[int | None] = mapped_column(Integer)

    # ─── Gravação ─────────────────────────────────────────────────────────
    gravacao_url: Mapped[str | None] = mapped_column(String(300))
    gravacao_hash: Mapped[str | None] = mapped_column(String(64))

    # ─── Relacionamentos ──────────────────────────────────────────────────
    atendimento: Mapped["Atendimento | None"] = relationship(back_populates="chamadas")
    canal_contratado: Mapped["CanalContratado | None"] = relationship()


__all__ = ["ChamadaPABX"]