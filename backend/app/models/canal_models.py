"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Canal
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal.py
@module   Backend / App / Models / Canal
@author   Aldemir Queiroz
@since    2026
@version  3.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa o PONTO DE ENTRADA pelo qual o CLIENTE FINAL entra em contato
com a EMPRESA que comprou o EcoChatBot-MA.

  • Se a empresa contratou só WhatsApp   → cliente entra só por WhatsApp
  • Se contratou WhatsApp + Telegram     → cliente entra por qualquer um
  • Se contratou WhatsApp + PABX + Email → cliente entra por qualquer um

É o mesmo conceito de "Inbox" do Chatwoot: um canal = uma porta de entrada.

❌ NÃO é departamento.
❌ NÃO é fila de atendimento.
❌ NÃO é tipo de atendimento ("agendamento", "financeiro").
   Isso é responsabilidade de `Menu` / `MenuOpcao` → `Departamento`.

EXEMPLO PRÁTICO
───────────────
    Empresa: Mackenzie Hospital
    ├── Telefone("556734167800")
    │     ├── Canal(tipo="whatsapp",  apelido="WhatsApp Recepção")
    │     └── Canal(tipo="telegram",  apelido="Telegram Suporte")
    ├── Telefone("5567992469894")
    │     └── Canal(tipo="whatsapp",  apelido="WhatsApp Agendamento")
    └── Canal(tipo="pabx",            apelido="URA do PABX")

    Ao entrar webhook do WhatsApp no telefone "556734167800":
        → sistema localiza o Canal(telefone_id=1, tipo="whatsapp")
        → carrega o Menu DAQUELE canal
        → cliente escolhe opção → resolve Departamento → abre Atendimento

REGRAS DE NEGÓCIO
─────────────────
    • Unicidade: 1 tipo por TELEFONE — não pode haver 2 WhatsApp no mesmo
      número. Com um 2º telefone, a empresa PODE contratar um 2º WhatsApp
      (e a mensalidade é duplicada).
    • `telefone_id` é obrigatório — canal sem telefone é recusado com 403.
    • `credenciais` guarda tokens/IDs em JSON (criptografar em produção).
    • `webhook_token` valida a origem do webhook recebido.
    • Soft delete: desativar contrato NÃO apaga histórico de mensagens.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.conexao_models import Conexao
    from app.models.empresa_models import Empresa
    from app.models.menu_models import Menu
    from app.models.telefone_models import Telefone
    from app.models.usuario_canal_models import UsuarioCanal


class Canal(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Ponto de entrada do cliente final (mesmo conceito de Inbox do Chatwoot).

    Cada registro representa: "esta empresa recebe mensagens por este canal".
    """

    __tablename__ = "canais"
    __table_args__ = (
        UniqueConstraint(
            "telefone_id", "tipo",
            name="uq_canais_telefone_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # `empresa_id` vem do TenantMixin — é o filtro Anti-IDOR de TODA query.

    telefone_id: Mapped[int] = mapped_column(
        ForeignKey("telefones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Telefone que sustenta este canal — eixo da contratação",
    )

    # ─── Tipo do canal ────────────────────────────────────────────────────
    # String(20) livre — novos tipos (signal, matrix, etc.) não exigem
    # migration. A validação de tipo é feita no schema (Literal TipoCanal).
    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="whatsapp | telegram | instagram | facebook | pabx | discord | email | chat_web",
    )

    # ─── Identificação amigável ───────────────────────────────────────────
    apelido: Mapped[str | None] = mapped_column(
        String(80),
        comment='Ex.: "WhatsApp Comercial", "Telegram Suporte"',
    )

    # ─── Credenciais (JSON serializado — criptografar em produção) ────────
    credenciais: Mapped[str | None] = mapped_column(
        Text,
        comment='Ex.: {"phone_number": "556734167800", "token": "..."}',
    )

    # ─── Webhook ──────────────────────────────────────────────────────────
    webhook_token: Mapped[str | None] = mapped_column(String(120), index=True)
    webhook_url: Mapped[str | None] = mapped_column(String(300))

    # ─── Expediente do canal (opcional — sobrepõe o do departamento) ──────
    horario_inicio: Mapped[str | None] = mapped_column(String(5))   # "08:00"
    horario_fim: Mapped[str | None] = mapped_column(String(5))      # "18:00"
    dias_semana: Mapped[str | None] = mapped_column(String(20))     # "1,2,3,4,5"

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="canais")
    telefone: Mapped["Telefone"] = relationship(back_populates="canais")

    conexoes: Mapped[List["Conexao"]] = relationship(
        back_populates="canal", cascade="all, delete-orphan"
    )
    menus: Mapped[List["Menu"]] = relationship(
        back_populates="canal", cascade="all, delete-orphan"
    )
    atendimentos: Mapped[List["Atendimento"]] = relationship(
        back_populates="canal"
    )
    vinculos_usuario: Mapped[List["UsuarioCanal"]] = relationship(
        back_populates="canal", cascade="all, delete-orphan"
    )

    # ─── Dunder ───────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Canal id={self.id} tipo={self.tipo!r} "
            f"apelido={self.apelido!r} empresa_id={self.empresa_id}>"
        )


__all__ = ["Canal"]