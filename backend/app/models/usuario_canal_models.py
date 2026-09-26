"""
================================================================================
MÓDULO: app/models/usuario_canal_models.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 0.1.0
OBJETIVO: Vínculo entre o atendente e os canais que ele pode atender. Decide,
          por dado, se o atendente atende UM canal ou VÁRIOS.
PASTA: backend/app/models/
================================================================================

FUNCIONALIDADE
──────────────
    Vincula um `Usuario` a um `CanalContratado`. O gestor da empresa opera essa
    configuração: um atendente pode estar restrito a um único canal ou atender
    em vários. A mesma estrutura serve os dois casos — um atendente com um
    único vínculo atende um canal; com vários vínculos, atende vários.

EXEMPLO PRÁTICO
───────────────
    Gestor decide: atendente Ana atende SOMENTE WhatsApp
        Vinculo(Ana, CanalContratado(whatsapp), principal=True)

    Gestor decide: atendente Bruno atende WhatsApp, Telegram e PABX
        Vinculo(Bruno, CanalContratado(whatsapp), principal=True)
        Vinculo(Bruno, CanalContratado(telegram), principal=False)
        Vinculo(Bruno, CanalContratado(pabx),    principal=False)

    `principal` indica por qual canal o atendente é notificado primeiro.
    A restriction de "no máximo um principal por usuário" é do Service, não do
    banco, porque o banco não sabe o que é "principal" sem regra de negócio.

RELACIONAMENTO
──────────────
    Usuario (1) ── (N) UsuarioCanal ── (1) CanalContratado (1) ── (N) Telefone
                                       │
                                       └── (N) Atendimento
                                              (originados nos canais do usuario)

REGRAS DE NEGÓCIO
─────────────────
    • Unicidade: um usuário não pode ter dois vínculos para o MESMO canal
    • Ao remover o vínculo, o histórico de atendimentos é preservado
    • Desativar o vínculo (`ativo=False`) tira o atendente da fila daquele
      canal sem apagar o passado
================================================================================
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_models import CanalContratado
    from app.models.usuario_models import Usuario


class UsuarioCanal(TimestampMixin, Base):
    """Vínculo de um atendente com um canal contratado."""

    __tablename__ = "usuarios_canais"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "canal_contratado_id", name="uq_usuarios_canais_vinculo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("canais_contratados.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    principal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="vinculos_canal")
    canal: Mapped["CanalContratado"] = relationship(back_populates="vinculos_usuario")
