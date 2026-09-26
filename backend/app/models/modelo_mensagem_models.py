"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Modelo de Mensagem (Template)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     modelo_mensagem_models.py
@module   Backend / App / Models / Modelo Mensagem
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Armazena TEMPLATES de mensagem reutilizáveis — textos que o bot, o
atendente ou uma campanha podem enviar, com variáveis substituíveis.

EXEMPLO PRÁTICO
───────────────
    ModeloMensagem(
        chave="boas_vindas",
        conteudo="Olá, {nome}! 👋 Bem-vindo à {empresa}.",
        variaveis="nome,empresa",
        canal_tipo="whatsapp",
    )

    No envio:
        texto = template.render(nome="João", empresa="Aldemir Ltda")

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) ModeloMensagem
    Campanha  (N) ── (1) ModeloMensagem  (opcional)

REGRAS DE NEGÓCIO
─────────────────
    • `chave` única por empresa (ex.: "boas_vindas", "fora_expediente")
    • `variaveis` é CSV das chaves esperadas — usado para validação
    • Se `canal_tipo` for NULL → modelo agnóstico (serve em todos)
    • Se `canal_tipo` for "whatsapp" → só usado no WhatsApp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoMensagem
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    pass


class ModeloMensagem(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """Template de mensagem com variáveis substituíveis."""

    __tablename__ = "modelos_mensagem"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "chave",
            name="uq_modelos_mensagem_empresa_chave",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    chave: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)

    # ─── Conteúdo ─────────────────────────────────────────────────────────
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    variaveis: Mapped[str | None] = mapped_column(Text)   # CSV: "nome,empresa"
    tipo: Mapped[str] = mapped_column(
        String(20), default=TipoMensagem.TEXTO.value, nullable=False
    )

    # ─── Escopo ───────────────────────────────────────────────────────────
    canal_tipo: Mapped[str | None] = mapped_column(String(20))
    # NULL = todos os canais; senão, só para aquele canal

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    # (nenhum por enquanto — campanhas referenciam via chave)


__all__ = ["ModeloMensagem"]