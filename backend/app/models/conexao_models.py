"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Conexão
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     conexao_models.py
@module   Backend / App / Models / Conexao
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Registra o ESTADO e o HISTÓRICO de conexões do CanalContratado com o
provedor externo (WhatsApp Cloud API, Evolution API, Telegram Bot API,
Asterisk/PABX etc.).

Cada tentativa de conexão gera UM registro — assim é possível auditar:
    • Quando o canal caiu
    • Quantas reconexões ocorreram
    • Qual o último erro (se houver)

RELACIONAMENTO
──────────────
    CanalContratado (1) ── (N) Conexao

    A conexão ATIVA de um canal é a de maior `iniciada_em` com
    `status='conectado'` e `encerrada_em IS NULL`.

REGRAS DE NEGÓCIO
─────────────────
    • Não guardar credenciais aqui — apenas metadados da sessão
    • `payload_erro` é JSON com detalhes técnicos (usado em debugging)
    • Conexões antigas podem ser arquivadas por rotina de limpeza
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusConexao
from app.models.mixins import TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_contratado_models import CanalContratado


class Conexao(TimestampMixin, TenantMixin, Base):
    """
    Registro de uma sessão de conexão do canal com o provedor externo.

    Não herda SoftDeleteMixin: conexões antigas devem permanecer para
    auditoria — se necessário, uma rotina de expurgo as remove fisicamente.
    """

    __tablename__ = "conexoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    canal_contratado_id: Mapped[int] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Ciclo de vida ────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusConexao.DESCONECTADO.value, nullable=False, index=True
    )
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    encerrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Diagnóstico ──────────────────────────────────────────────────────
    mensagem: Mapped[str | None] = mapped_column(String(300))
    payload_erro: Mapped[str | None] = mapped_column(Text)   # JSON com stack
    tentativas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ─── Endereço remoto (opcional) ───────────────────────────────────────
    host_remoto: Mapped[str | None] = mapped_column(String(120))
    ip_remoto: Mapped[str | None] = mapped_column(String(45))   # IPv6 cabe

    # ─── Relacionamentos ──────────────────────────────────────────────────
    canal_contratado: Mapped["CanalContratado"] = relationship(back_populates="conexoes")


__all__ = ["Conexao"]