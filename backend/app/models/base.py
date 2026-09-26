"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Base Declarativa do ORM
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     base.py
@module   Backend / App / Models / Base
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define a classe `Base` (DeclarativeBase do SQLAlchemy 2.0) usada por TODOS
os modelos. Centraliza:

    • Convenção de nomes de constraints → evita conflitos no Alembic
    • Metadados compartilhados (Base.metadata)
    • __repr__ legível em logs

POR QUE IMPORTA
───────────────
Sem a NAMING_CONVENTION, o Alembic gera nomes aleatórios para FKs/índices
(ex.: "fk_1234abc"), quebrando migrações em produção. Com ela, todo
constraint tem nome determinístico.

RELACIONAMENTO
──────────────
    base.py
        ├──► herdado por TODOS os *_models.py
        └──► importado em alembic/env.py para autogenerate

USO
───
    from app.models.base import Base

    class MinhaEntidade(Base):
        __tablename__ = "minhas_entidades"
        id: Mapped[int] = mapped_column(primary_key=True)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# ─── Convenção determinística de nomes (Alembic-friendly) ─────────────────
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base declarativa do SQLAlchemy 2.0.

    Todas as entidades do sistema herdam desta classe. Isso garante
    que `Base.metadata` conheça TODAS as tabelas — pré-requisito para
    o Alembic autogenerate funcionar corretamente.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def __repr__(self) -> str:  # pragma: no cover
        pk = getattr(self, "id", None)
        return f"<{self.__class__.__name__} id={pk}>"


__all__ = ["Base", "NAMING_CONVENTION"]