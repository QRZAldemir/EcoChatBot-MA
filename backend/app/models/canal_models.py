"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Canal Contratado
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal_contratado_models.py
@module   Backend / App / Models / Canal Contratado
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa um ITEM DO CONTRATO da Empresa. Cada registro aqui significa:
"esta Empresa PAGA para receber mensagens por este canal".

EXEMPLO PRÁTICO
───────────────
    Empresa: Aldemir Ltda
    ├── Telefone(numero="556734167800", principal=True)
    │     ├── CanalContratado(tipo="whatsapp", ativo=True)   ✅
    │     └── CanalContratado(tipo="telegram", ativo=True)   ✅
    ├── Telefone(numero="5567992469894")
    │     └── CanalContratado(tipo="whatsapp", ativo=True)   ✅  2º whatsapp
    └── (canal sem telefone → sistema REJEITA com 403)

    Se chegar webhook do Facebook → sistema REJEITA com 403.

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Telefone ── (N) CanalContratado
                                          │
                                          ├── (N) Conexao      (status/histórico do socket)
                                          ├── (N) Atendimento  (mensagens recebidas)
                                          └── (N) Menu         (menu específico do canal)

REGRAS DE NEGÓCIO
─────────────────
    • Unicidade: 1 tipo por TELEFONE — não pode haver 2 WhatsApp no mesmo
      número. Com um 2º telefone, a Empresa PODE contratar um 2º WhatsApp
      (e a mensalidade é duplicada).
    • O canal SEMPRE pertence a um telefone: `telefone_id` é obrigatório
    • `credenciais` guarda tokens/IDs em JSON (criptografar em produção)
    • `webhook_token` valida a origem do webhook recebido
    • Soft delete: desativar contrato NÃO apaga histórico de mensagens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoCanalMensageria
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.usuario_canal_models import UsuarioCanal
    from app.models.atendimento_models import Atendimento
    from app.models.conexao_models import Conexao
    from app.models.empresa_models import Empresa
    from app.models.menu_models import Menu
    from app.models.telefone_models import Telefone


class CanalContratado(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Item do contrato: a Empresa paga para receber mensagens por este canal.

    Corresponde ao "quanto de canal" a empresa contratou. Se contratou
    apenas WhatsApp, só existe 1 registro aqui.
    """

    __tablename__ = "canais_contratados"
    __table_args__ = (
        UniqueConstraint(
            "telefone_id", "tipo",
            name="uq_canais_contratados_telefone_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telefone_id: Mapped[int] = mapped_column(
        ForeignKey("telefones.id", ondelete="CASCADE"), nullable=False, index=True,
        comment="Telefone que sustenta este canal — eixo da contratação",
    )

    # ─── Tipo do canal ────────────────────────────────────────────────────
    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )   # whatsapp | telegram | instagram | facebook | pabx | discord | email

    # ─── Identificação amigável ───────────────────────────────────────────
    apelido: Mapped[str | None] = mapped_column(String(80))
    # ex.: "WhatsApp Comercial", "Telegram Suporte"

    # ─── Credenciais (JSON criptografado em produção) ─────────────────────
    credenciais: Mapped[str | None] = mapped_column(Text)
    # ex.: {"phone_id": "...", "token": "..."} para WhatsApp
    #      {"bot_token": "..."}                  para Telegram

    # ─── Webhook ──────────────────────────────────────────────────────────
    webhook_token: Mapped[str | None] = mapped_column(String(120), index=True)
    webhook_url: Mapped[str | None] = mapped_column(String(300))

    # ─── Expediente do canal (opcional — sobrepõe o do departamento) ──────
    horario_inicio: Mapped[str | None] = mapped_column(String(5))   # "08:00"
    horario_fim: Mapped[str | None] = mapped_column(String(5))      # "18:00"
    dias_semana: Mapped[str | None] = mapped_column(String(20))     # "1,2,3,4,5"

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="canais_contratados")
    telefone: Mapped["Telefone"] = relationship(back_populates="canais")
    conexoes: Mapped[List["Conexao"]] = relationship(
        back_populates="canal_contratado", cascade="all, delete-orphan"
    )
    menus: Mapped[List["Menu"]] = relationship(
        back_populates="canal_contratado", cascade="all, delete-orphan"
    )
    atendimentos: Mapped[List["Atendimento"]] = relationship(
        back_populates="canal_contratado"
    )
    vinculos_usuario: Mapped[List["UsuarioCanal"]] = relationship(
        back_populates="canal", cascade="all, delete-orphan"
    )


__all__ = ["CanalContratado"]