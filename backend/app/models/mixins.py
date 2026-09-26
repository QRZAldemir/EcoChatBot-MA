"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Mixins Reutilizáveis do ORM
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     mixins.py
@module   Backend / App / Models / Mixins
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define mixins que podem ser combinados em qualquer entidade ORM:

    • TimestampMixin  → created_at + updated_at (server-side defaults)
    • SoftDeleteMixin → deleted_at + is_deleted + soft_delete() + restore()
    • TenantMixin     → cliente_id (FK para `clientes.id`)

POR QUE MIXINS?
───────────────
Sem eles, TODA tabela repetiria colunas como `created_at`, `updated_at`,
`deleted_at` e `cliente_id`. Com mixins, a regra vive em um só lugar —
correção aplicada aqui vale para todas as entidades.

REGRA DE USO
────────────
    class MinhaEntidade(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
        __tablename__ = "minhas_entidades"
        ...

⚠️ Atenção à ordem: Base deve vir por ÚLTIMO na herança.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    """Retorna o 'agora' UTC timezone-aware (evita datetime.utcnow())."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Adiciona auditoria temporal básica.

    created_at  → preenchido pelo banco (server_default=func.now())
    updated_at  → atualizado automaticamente em cada UPDATE (onupdate)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Exclusão lógica: a linha nunca é apagada fisicamente.

    Isso preserva histórico de atendimentos, auditoria LGPD e
    integridade de relatórios analíticos.

    Uso:
        obj.soft_delete()   # marca deleted_at
        obj.restore()       # limpa deleted_at
        obj.is_deleted      # property → bool
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        """True se a entidade foi marcada como excluída."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca a entidade como excluída (sem remover do banco)."""
        self.deleted_at = _utcnow()

    def restore(self) -> None:
        """Desfaz o soft delete."""
        self.deleted_at = None


class TenantMixin:
    """
    Isolamento multi-tenant: toda entidade pertence a um Cliente.

    A FK aponta para `clientes.id`. Entidades que NÃO pertencem a um
    cliente específico (ex.: `Cliente` em si) NÃO herdam este mixin.

    ⚠️ Ao herdar, garanta que a tabela `clientes` já existe no metadata.
    """

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


__all__ = ["TimestampMixin", "SoftDeleteMixin", "TenantMixin", "_utcnow"]