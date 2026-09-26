"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Mixins Reutilizáveis do ORM
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

    • TimestampMixin  → criado_em + atualizado_em (server-side defaults)
    • SoftDeleteMixin → deleted_at + is_deleted + soft_delete() + restore()
    • TenantMixin     → empresa_id (FK para `empresas.id`) — a Empresa é o tenant

POR QUE MIXINS?
───────────────
Sem eles, TODA tabela repetiria colunas como `criado_em`, `atualizado_em`,
`deleted_at` e `empresa_id`. Com mixins, a regra vive em um só lugar —
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

    criado_em     → preenchido pelo banco (server_default=func.now())
    atualizado_em → atualizado automaticamente em cada UPDATE (onupdate)

    POR QUE `criado_em` E NÃO `created_at`?
    ---------------------------------------
    O banco em produção já se chama `criado_em`, e o código legado inteiro
    (69 chamadas) lê e escreve por esse nome. Emitir `created_at` aqui criaria
    uma segunda nomenclatura e obrigaria a traduzir em todo serviço. O mixin
    segue o banco: um nome só, em todo o projeto.
    """

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
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
    Isolamento multi-tenant: toda entidade pertence a uma EMPRESA.

    A FK aponta para `empresas.id`.

    POR QUE `empresa_id` E NÃO `cliente_id`?
    ---------------------------------------
    O modelo tinha as DUAS colunas ao mesmo tempo em 13 tabelas, e nenhuma
    criteriava qual era a verdadeira — o isolamento do tenant ficava
    ambíguo. A decisão é: **a Empresa é o tenant**. Toda linha operacional
    pertence a uma empresa, e é por `empresa_id` que se filtra.

    `Cliente` continua existindo, mas NÃO é tenant: é a conta COMERCIAL que
    contrata e agrupa empresas (`plano`, `limite_empresas`, `limite_usuarios`).
    Por isso `empresas.cliente_id` continua existindo — é o pai comercial,
    não o tenant. Quem filtra dado do cliente vai por `Cliente → Empresa`.

    ⚠️ Entidades que NÃO pertencem a uma empresa (o próprio `Cliente` e a
    própria `Empresa`) NÃO herdam este mixin.
    """

    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


__all__ = ["TimestampMixin", "SoftDeleteMixin", "TenantMixin", "_utcnow"]