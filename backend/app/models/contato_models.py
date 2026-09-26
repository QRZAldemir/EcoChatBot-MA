"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Contato
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
PABX) — por isso a unicidade é (empresa_id, canal_tipo, canal_identificador)
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

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.empresa_models import Empresa


class Contato(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Pessoa que interage com o sistema em qualquer canal."""

    __tablename__ = "contatos"
    # SEM UniqueConstraint de canal aqui. A identidade por canal é responsibility
    # de `ContatoCanal`; o UNIQUE (empresa, canal_tipo, canal_identificador) que
    # existia aqui impedia a PESSOA de existir em mais de um canal e, como os
    # campos eram NOT NULL, impedia um contato sem canal (lead de campanha)
    # existir. Ver `ContatoCanal`.

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str | None] = mapped_column(String(150), index=True)
    apelido: Mapped[str | None] = mapped_column(String(80))

    # ─── Chave no canal (ATUALIZADA) ──────────────────────────────────────
    # Antigamente NOT NULL, o que contradizia o docstring desta classe ("um mesmo
    # Contato pode existir em vários canais") e impedia criar um lead sem canal.
    # São agora um par opcional e apenas INFORMATIVO: a identidade canônica por
    # canal está em `ContatoCanal` (`identificador` + `canal_contratado_id`).
    # Mantidos aqui para busca por canal sem JOIN e para integração legada.
    canal_tipo: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    canal_identificador: Mapped[str | None] = mapped_column(
        String(120), nullable=True, index=True
    )

    # ─── Contato tradicional ──────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(20))

    # ─── Metadados ────────────────────────────────────────────────────────
    tags: Mapped[str | None] = mapped_column(Text)   # CSV simples
    notas: Mapped[str | None] = mapped_column(Text)
    ultima_interacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship()
    atendimentos: Mapped[List["Atendimento"]] = relationship(
        back_populates="contato", cascade="all, delete-orphan"
    )
    canais: Mapped[List["ContatoCanal"]] = relationship(
        back_populates="contato", cascade="all, delete-orphan"
    )


class ContatoCanal(TimestampMixin, Base):
    """Identidade de uma PESSOA em um CANAL CONTRATADO específico.

    Equivale ao `contact_inboxes` do Chatwoot, e segue a mesma ideia do
    `@@unique([remoteJid, instanceId])` do Evolution (ver `Contact` no
    `postgresql-schema.prisma`): a MESMA pessoa em canais diferentes são
    identidades DISTINTAS, porque o mesmo número podeSignificantemente não ser
    a mesma coisa em dois números da empresa.

    SEM `empresa_id` (o escopo vem por `contato_id -> contatos.empresa_id`),
    igual ao `contact_inboxes` do Chatwoot e ao `Contact` do Evolution, que não
    duplica o escopo do pai. Em troca, TODA query de escopo precisa passar pelo
    JOIN com `contatos` — ver `ContatoService`, que faz isso em todo acesso.
    """

    __tablename__ = "contato_canais"
    __table_args__ = (
        # A MESMA constraint do Evolution: um identificador por canal, não
        # global. Sem `canal_contratado_id` no UNIQUE, o contato de duas
        # unidades diferentes colidiria.
        UniqueConstraint(
            "canal_contratado_id", "identificador",
            name="uq_contato_canais_canal_identificador",
        ),
        # Busca por identificador sem saber o canal (ex.: webhook chegando).
        Index("ix_contato_canais_identificador", "identificador"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    contato_id: Mapped[int] = mapped_column(
        ForeignKey("contatos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # `remoteJid` no Evolution (5511999999999@s.whatsapp.net), `source_id` no
    # Chatwoot. O mesmo número em dois canais -> duas linhas, sem conflito.
    identificador: Mapped[str] = mapped_column(String(120), nullable=False)
    # `pushName` no Evolution: o nome que o canal EXIBE, que nem sempre bate com
    # o nome real da pessoa.
    push_name: Mapped[str | None] = mapped_column(String(150))

    contato: Mapped["Contato"] = relationship(back_populates="canais")
    canal_contratado: Mapped["CanalContratado"] = relationship()


__all__ = ["Contato", "ContatoCanal"]