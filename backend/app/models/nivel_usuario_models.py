"""
================================================================================
MÓDULO: app/models/nivel_usuario_models.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 0.1.0
OBJETIVO: Catálogo de níveis de acesso do atendente, referenciado por
          `Usuario.nivel_id`. Sem este model a FK do Usuario ficaria órfã.
PASTA: backend/app/models/
================================================================================

FUNCIONALIDADE
──────────────
    Define os níveis de permissão que o gestor da empresa pode atribuir a um
    atendente. O nível controla o que a pessoa pode fazer, e é independente do
    canal em que ela atende.

RELACIONAMENTO
──────────────
    NivelUsuario (1) ── (N) Usuario
    Usuario (1) ── (N) UsuarioCanal ── (1) CanalContratado

REGRAS DE NEGÓCIO
─────────────────
    • `nome` é único: não pode existir dois níveis com o mesmo nome
    • Ordem de permissão é feita pelo Service, comparando a ordem dos níveis
      configurados, e não por valor mágico no banco
    • Desativar um nível não apaga usuários: o `ativo` é do vínculo do usuário
================================================================================
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.usuario_models import Usuario


class NivelUsuario(Base):
    """Nível de acesso de um atendente."""

    __tablename__ = "nivel_usuario"
    __table_args__ = (
        UniqueConstraint("nome", name="uq_nivel_usuario_nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(200))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="nivel")


__all__ = ["NivelUsuario"]
