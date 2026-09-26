"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Roteiro
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     roteiro_models.py
@module   Backend / App / Models / Roteiro
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Registra METADADOS de um roteiro — o arquivo HTML com as perguntas que
o cliente responde após escolher uma opção do menu.

CONFORME README, SEÇÃO 3
────────────────────────
    ROTEIRO = "Arquivo com perguntas e fluxo específicos"
    Exemplos: pedidos.html, suporte.html, agendamento.html

O CONTEÚDO do roteiro NÃO fica no banco — fica em arquivo HTML no
diretório `roteiros/` (conforme estrutura do projeto). Aqui só fica:
    • Nome lógico
    • Caminho do arquivo
    • Status (rascunho/ativo)
    • Hash SHA-256 do arquivo (detecta alterações externas)

RELACIONAMENTO
──────────────
    Roteiro (1) ── (N) MenuItem   (um roteiro pode ser usado por vários itens)

REGRAS DE NEGÓCIO
─────────────────
    • Se o arquivo não existe no disco → status vira `inativo` automaticamente
    • O parser do `roteiro_service.py` lê o HTML e extrai os campos
    • `hash_arquivo` é recalculado em cada validação (detecta edições manuais)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusRoteiro
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_models import MenuItem


class Roteiro(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Metadados de um roteiro HTML.

    Não confundir: o ARQUIVO HTML vive em `roteiros/`, este modelo só
    aponta para ele e guarda estado.
    """

    __tablename__ = "roteiros"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    # ex.: "agendamento_ambulatorial"
    titulo_exibicao: Mapped[str | None] = mapped_column(String(200))
    # ex.: "Agendamento Ambulatorial"
    descricao: Mapped[str | None] = mapped_column(Text)

    # ─── Arquivo ──────────────────────────────────────────────────────────
    arquivo: Mapped[str] = mapped_column(String(300), nullable=False)
    # ex.: "roteiros/agendamento.html"
    hash_arquivo: Mapped[str | None] = mapped_column(String(64))
    # SHA-256 do conteúdo — detecta edições manuais
    total_perguntas: Mapped[int] = mapped_column(Integer, default=0)

    # ─── Estado ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=StatusRoteiro.RASCUNHO.value, nullable=False, index=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    menu_itens: Mapped[List["MenuItem"]] = relationship(back_populates="roteiro")


__all__ = ["Roteiro"]