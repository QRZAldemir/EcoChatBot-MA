"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Contexto do Atendimento
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_context_models.py
@module   Backend / App / Models / Atendimento Contexto
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Armazena, em formato CHAVE-VALOR, todas as RESPOSTAS que o cliente deu
ao roteiro (formulário HTML) durante o atendimento.

É o "formulário preenchido" que o atendente vê ao abrir o painel.

EXEMPLO PRÁTICO
───────────────
    Atendimento #1234 (Agendamento Ambulatorial)
    ├── Contexto("nome_completo",    "João da Silva")
    ├── Contexto("cpf",              "123.456.789-00")
    ├── Contexto("data_nascimento",  "1980-05-12")
    └── Contexto("especialidade",    "Cardiologia")

RELACIONAMENTO
──────────────
    Atendimento (1) ── (N) AtendimentoContexto

    Cada pergunta do roteiro vira 1 linha aqui.

REGRAS DE NEGÓCIO
─────────────────
    • Chave única por atendimento: (atendimento_id, chave)
    • `tipo` permite validação posterior (data, número, email)
    • `origem` distingue o que veio do roteiro vs digitado pelo atendente
    • `ordem` preserva a sequência do roteiro para exibição fiel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoPergunta
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento


class AtendimentoContexto(TimestampMixin, Base):
    """
    Resposta individual de uma pergunta do roteiro.

    Padrão EAV (Entity-Attribute-Value) restrito — cada linha é uma
    resposta. Não é um "JSON solto" para permitir consultas:
        SELECT * FROM atendimento_contextos
        WHERE chave='cpf' AND valor LIKE '%123%'
    """

    __tablename__ = "atendimento_contextos"
    __table_args__ = (
        UniqueConstraint(
            "atendimento_id", "chave",
            name="uq_atendimento_contexto_chave",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    atendimento_id: Mapped[int] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Pergunta/Resposta ────────────────────────────────────────────────
    chave: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # ex.: "nome_completo", "cpf", "especialidade"
    pergunta: Mapped[str | None] = mapped_column(String(300))
    # texto exato exibido ao cliente
    valor: Mapped[str | None] = mapped_column(Text)

    # ─── Tipo ─────────────────────────────────────────────────────────────
    tipo: Mapped[str] = mapped_column(
        String(20), default=TipoPergunta.TEXTO.value, nullable=False
    )

    # ─── Origem ───────────────────────────────────────────────────────────
    origem: Mapped[str] = mapped_column(
        String(20), default="roteiro", nullable=False
    )   # roteiro | atendente | api

    # ─── Metadados ────────────────────────────────────────────────────────
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    obrigatorio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    atendimento: Mapped["Atendimento"] = relationship(back_populates="contextos")


__all__ = ["AtendimentoContexto"]