# backend/app/models/base.py
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Base Declarativa do ORM
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     base.py
@module   Backend / App / Models
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FUNCIONALIDADE
──────────────
Define a classe `Base` (DeclarativeBase do SQLAlchemy 2.0) usada por TODOS
os modelos. Centraliza:

    • Convenção de nomes de constraints → evita conflitos no Alembic
    • Metadados compartilhados (Base.metadata)
    • __repr__ legível em logs
    • Timestamps automáticos para criação e atualização
    • Métodos utilitários comuns

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
        created_at: Mapped[datetime] = mapped_column(
            default=datetime.utcnow,
            nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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

    Atributos:
        metadata: Metadados compartilhados com convenção de nomes
        created_at: Timestamp automático de criação
        updated_at: Timestamp automático de atualização
    """
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # ─── Timestamps automáticos ─────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
        comment="Registro de quando o registro foi criado"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Registro de quando o registro foi atualizada pela última vez"
    )

    def __repr__(self) -> str:  # pragma: no cover
        """
        Representação string da entidade.
        
        Inclui o nome da classe e o valor da chave primária, se existir.
        """
        pk = getattr(self, "id", None)
        return f"<{self.__class__.__name__} id={pk}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a entidade para um dicionário.
        
        Retorna:
            Dicionário com todos os campos da entidade, exceto campos internos.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if not column.name.startswith('_')
        }

    def before_update(self) -> None:
        """
        Hook executado antes de atualizar a entidade.
        
        Pode ser sobrescrito por subclasses para adicionar lógica customizada.
        """
        self.updated_at = datetime.utcnow()

    def before_insert(self) -> None:
        """
        Hook executado antes de inserir a entidade.
        
        Pode ser sobrescrito por subclasses para adicionar lógica customizada.
        """
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()

__all__ = ["Base", "NAMING_CONVENTION"]
