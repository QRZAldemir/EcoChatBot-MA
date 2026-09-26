"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Empresa · Usuario · InstanciaChatbot
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     empresa_models.py
@module   Backend / App / Models / Empresa
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Este arquivo agrupa TRÊS entidades estreitamente relacionadas:

    1. Empresa          → unidade de negócio dentro de um Cliente
    2. Usuario          → operador (admin, atendente, bot, API)
    3. InstanciaChatbot → configuração de um bot (prompt, modelo LLM)

Agrupamento justificado: InstanciaChatbot pertence a Empresa, e Usuario
também — mantê-los juntos evita fragmentação desnecessária.

RELACIONAMENTO
──────────────
    Cliente (1) ── (N) Empresa (1) ── (N) Usuario
                                 ├── (N) InstanciaChatbot
                                 ├── (N) Departamento
                                 └── (N) CanalMensageria

REGRAS DE NEGÓCIO
─────────────────
    • Slug de Empresa é único DENTRO do Cliente (não global)
    • Email de Usuario é único DENTRO do Cliente
    • Usuario.empresa_id é nullable → permite super_admin "solto"
    • InstanciaChatbot herda TenantMixin (cliente_id) + empresa_id
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PerfilUsuario
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.cliente_models import Cliente
    from app.models.departamento_models import Departamento


class Empresa(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Unidade de negócio dentro de um Cliente.

    Exemplos: "Filial SP", "Filial RJ", "Loja Centro".
    """

    __tablename__ = "empresas"
    __table_args__ = (
        UniqueConstraint("cliente_id", "slug", name="uq_empresas_cliente_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Identificação ────────────────────────────────────────────────────
    razao_social: Mapped[str] = mapped_column(String(200), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cnpj: Mapped[str | None] = mapped_column(String(18))

    # ─── Contato ──────────────────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(20))

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship(back_populates="empresas")
    usuarios: Mapped[List["Usuario"]] = relationship(
        back_populates="empresa", cascade="all, delete-orphan"
    )
    departamentos: Mapped[List["Departamento"]] = relationship(
        back_populates="empresa", cascade="all, delete-orphan"
    )
    instancias: Mapped[List["InstanciaChatbot"]] = relationship(
        back_populates="empresa", cascade="all, delete-orphan"
    )


class Usuario(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Operador do sistema.

    Perfis (ver `PerfilUsuario`):
        super_admin, admin, gestor, atendente, bot, api
    """

    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("cliente_id", "email", name="uq_usuarios_cliente_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int | None] = mapped_column(
        ForeignKey("empresas.id", ondelete="SET NULL"), index=True
    )

    # ─── Dados pessoais ───────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20))

    # ─── Acesso ───────────────────────────────────────────────────────────
    perfil: Mapped[str] = mapped_column(
        String(20), default=PerfilUsuario.ATENDENTE.value, nullable=False, index=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa | None"] = relationship(back_populates="usuarios")


class InstanciaChatbot(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Configuração de UM bot vinculado a uma Empresa.

    Cada Empresa pode ter N bots — por exemplo:
        • "Suporte"     → prompt técnico
        • "Vendas"      → prompt comercial
        • "Agendamento" → prompt de agenda
    """

    __tablename__ = "instancias_chatbot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ─── Identificação ────────────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)

    # ─── Configuração do LLM ──────────────────────────────────────────────
    system_prompt: Mapped[str | None] = mapped_column(Text)
    modelo_llm: Mapped[str] = mapped_column(String(80), default="deepseek-chat")
    temperatura: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="instancias")


__all__ = ["Empresa", "Usuario", "InstanciaChatbot"]