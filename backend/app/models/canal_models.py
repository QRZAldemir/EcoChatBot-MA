"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · CanalContratado
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal_models.py
@module   Backend / App / Models / CanalContratado
@author   Aldemir Queiroz
@since    2026
@version  4.0.0  · align ao ESTUDO_DE_CASO_CONTRATO_DE_CANAIS
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
    Empresa: Clinica Exemplo
    ├── Telefone("556734167800")
    │     ├── CanalContratado(tipo="whatsapp",  apelido="WhatsApp Recepção")
    │     └── CanalContratado(tipo="telegram",  apelido="Telegram Suporte")
    ├── Telefone("5567992469894")
    │     └── CanalContratado(tipo="whatsapp",  apelido="WhatsApp Agendamento")
    └── CanalContratado(tipo="pabx",            apelido="URA do PABX")

    Dois telefones podem ter dois WhatsApp — a mensalidade é duplicada.
    O mesmo telefone NÃO pode ter dois WhatsApp.

    Ao entrar webhook do WhatsApp no telefone "556734167800":
        → sistema localiza o CanalContratado(telefone_id=1, tipo="whatsapp")
        → carrega o Menu DAQUELE canal
        → cliente escolhe opção → resolve Departamento → abre Atendimento

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Telefone (1) ── (N) CanalContratado
                                              │
                                              ├── (N) Conexao
                                              ├── (N) Menu
                                              ├── (N) Atendimento
                                              └── (N) UsuarioCanal

    `CanalContratado` NUNCA aponta para `Departamento`. O destino do
    atendimento vem do `MenuItem` — ver ESTUDO_DE_CASO secao 2.

REGRAS DE NEGÓCIO
─────────────────
    • Unicidade: 1 tipo por TELEFONE — não pode haver 2 WhatsApp no mesmo
      número. Com um 2º telefone, a empresa PODE contratar um 2º WhatsApp
      (e a mensalidade é duplicada).
    • `telefone_id` é obrigatório — canal sem telefone é recusado com 403.
    • `credenciais` guarda tokens/IDs em JSON (criptografar em produção).
      É daqui que o adaptador de canal lê a credencial do tenant.
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


class CanalContratado(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Canal contratado — o produto que a empresa compra, vinculado a um telefone.

    Cada registro representa: "esta empresa comprou este canal, para este
    número". Não é departamento, não é fila, não é tipo de atendimento.
    """

    __tablename__ = "canais_contratados"
    __table_args__ = (
        UniqueConstraint(
            "telefone_id", "tipo",
            name="uq_canais_contratados_telefone_tipo",
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

    # ─── Credenciais do canal (JSON serializado — criptografar em produção) ──
    # É a fonte de verdade por tenant. O adaptador de canal
    # (`app/adapters`) recebe daqui o que o provedor exige:
    #     Evolution : {"instance": "...", "api_key": "..."}
    #     Meta Cloud: {"phone_number_id": "...", "access_token": "..."}
    #     Telegram  : {"bot_token": "..."}
    #     PABX/VoIP : {"base_url": "...", "api_key": "...", "auth_type": "bearer"}
    # Ausente = o adaptador cai nas variáveis de ambiente (tenant único / dev).
    credenciais: Mapped[str | None] = mapped_column(
        Text,
        comment='Ex.: {"instance": "ecochat", "api_key": "..."}',
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
    empresa: Mapped["Empresa"] = relationship(back_populates="canais_contratados")
    telefone: Mapped["Telefone"] = relationship(back_populates="canais_contratados")

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
        back_populates="canal_contratado", cascade="all, delete-orphan"
    )

    # ─── Dunder ───────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<CanalContratado id={self.id} tipo={self.tipo!r} "
            f"apelido={self.apelido!r} empresa_id={self.empresa_id}>"
        )


__all__ = ["CanalContratado"]