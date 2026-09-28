"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Atendimento
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_models.py
@module   Backend / App / Models / Atendimento
@author   Aldemir Queiroz
@since    2026
@version  3.0.0  · fix: telefone_id condicional + índices multi-tenant
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Representa UMA conversa em andamento entre o cliente e a empresa.
Coração do sistema — registro que aparece no painel do atendente.

FLUXO
─────
    1. Cliente envia mensagem (WhatsApp, Telegram, VoIP, ...)
    2. Sistema apresenta menu
    3. Cliente escolhe opção → cria Atendimento com:
         • canal_contratado (WhatsApp, Telegram, PABX...)
         • telefone_id (APENAS se o canal contratado for VoIP)
         • menu_item escolhido
         • departamento destino
    4. Roteiro é carregado → respostas em AtendimentoContexto
    5. Atendente designado → status EM_ANDAMENTO
    6. Atendente finaliza → status FINALIZADO

⚠️ REGRA DE NEGÓCIO CRÍTICA (v3.0.0)
────────────────────────────────────
`telefone_id` é CONDICIONAL AO CONTRATO:

    ┌──────────────────────────────────┬───────────────┐
    │ Canal contratado pela empresa    │ telefone_id   │
    ├──────────────────────────────────┼───────────────┤
    │ WhatsApp                         │ NULL          │
    │ Telegram                         │ NULL          │
    │ Instagram / Facebook / Discord   │ NULL          │
    │ PABX / VoIP (Asterisk, MicroSIP) │ NOT NULL      │
    └──────────────────────────────────┴───────────────┘

Por isso `telefone_id` é NULLABLE: só faz sentido quando o canal
contratado é de telefonia IP. Empresas sem VoIP NÃO têm telefone.

⚠️ CORREÇÃO DE SEGURANÇA (v3.0.0)
──────────────────────────────────
Índices compostos adicionados para dar suporte ao filtro multi-tenant
da consulta corrigida em `atendimento_service.listar()`:

    WHERE empresa_id = ? AND telefone_id = ? AND status = ?

REGRAS INVIOLÁVEIS
──────────────────
    • `empresa_id` (do TenantMixin) é NOT NULL e indexado
    • `telefone_id` é NULLABLE — só preenchido para canais VoIP
    • `canal_contratado_id` determina se `telefone_id` deve existir
      (validação é feita no service, não no banco)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
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
    from app.models.telefone_models import Telefone
    from app.models.transferencia_models import Transferencia


class Atendimento(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Conversa entre cliente e empresa em um canal contratado.

    `empresa_id` (do TenantMixin) é a chave de isolamento multi-tenant.
    `telefone_id` é opcional — depende do canal contratado ser VoIP.
    """

    __tablename__ = "atendimentos"

    # ═════════════════════════════════════════════════════════════════════
    # ÍNDICES COMPOSTOS (para a correção IDOR em listar())
    # ═════════════════════════════════════════════════════════════════════
    __table_args__ = (
        # Índice principal da busca por telefone (só usado em empresas
        # que contrataram VoIP — mas precisa existir para performance).
        Index(
            "ix_atendimentos_empresa_telefone_status",
            "empresa_id", "telefone_id", "status",
        ),
        # Índice auxiliar para listagens por tenant + status.
        Index(
            "ix_atendimentos_empresa_status",
            "empresa_id", "status",
        ),
        # Índice para o filtro por canal contratado.
        Index(
            "ix_atendimentos_empresa_canal",
            "empresa_id", "canal_contratado_id",
        ),
    )

    # ─── Chave primária ───────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── FKs de contexto ──────────────────────────────────────────────────
    contato_id: Mapped[int] = mapped_column(
        ForeignKey("contatos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ─── Telefone VoIP (CONDICIONAL — nullable) ───────────────────────────
    # Só é preenchido quando o canal contratado é de telefonia IP
    # (PABX/VoIP). Para WhatsApp/Telegram/Instagram/etc., fica NULL.
    telefone_id: Mapped[int | None] = mapped_column(
        ForeignKey("telefones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── Demais FKs ───────────────────────────────────────────────────────
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_itens.id", ondelete="SET NULL"),
        index=True,
    )
    departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL"),
        index=True,
    )
    atendente_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True,
    )

    # ─── Identificação ────────────────────────────────────────────────────
    protocolo: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True,
    )
    assunto: Mapped[str | None] = mapped_column(String(200))

    # ─── Estado ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        default=StatusAtendimento.AGUARDANDO.value,
        nullable=False,
        index=True,
    )
    prioridade: Mapped[str] = mapped_column(
        String(20),
        default=PrioridadeAtendimento.NORMAL.value,
        nullable=False,
    )
    origem: Mapped[str] = mapped_column(
        String(20),
        default=OrigemAtendimento.BOT.value,
        nullable=False,
    )

    # ─── Tempos ───────────────────────────────────────────────────────────
    iniciado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True,
    )
    primeira_resposta_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    finalizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True,
    )

    # ─── Conteúdo ─────────────────────────────────────────────────────────
    resumo: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship()
    contato: Mapped["Contato"] = relationship(back_populates="atendimentos")
    canal_contratado: Mapped["CanalContratado"] = relationship(
        back_populates="atendimentos",
    )
    telefone: Mapped["Telefone | None"] = relationship()
    menu_item: Mapped["MenuItem | None"] = relationship()
    departamento: Mapped["Departamento | None"] = relationship(
        back_populates="atendimentos",
    )
    atendente: Mapped["Usuario | None"] = relationship()

    contextos: Mapped[List["AtendimentoContexto"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan",
    )
    transferencias: Mapped[List["Transferencia"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan",
    )
    chamadas: Mapped[List["ChamadaPABX"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan",
    )

    # ═════════════════════════════════════════════════════════════════════
    # PROPRIEDADES AUXILIARES
    # ═════════════════════════════════════════════════════════════════════

    @property
    def eh_voip(self) -> bool:
        """
        True se este atendimento foi originado por canal VoIP.
        Útil para telas que mostram gravação de chamada, etc.
        """
        return self.telefone_id is not None


__all__ = ["Atendimento"]

# backend/app/models/atendimento_models.py
class Atendimento(Base):
    __tablename__ = "atendimentos"
    
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True) # OBRIGATÓRIO
    conexao_id = Column(Integer, ForeignKey("conexoes.id"), nullable=False, index=True) # OBRIGATÓRIO
    contato_id = Column(Integer, ForeignKey("contatos.id"), nullable=False)
    
    # ... outros campos ...

    empresa = relationship("Empresa")
    conexao = relationship("Conexao")
    contato = relationship("Contato")