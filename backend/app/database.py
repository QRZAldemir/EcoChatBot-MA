"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Database Connection (PostgreSQL)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     database.py
@module   Backend / App / Config
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Configuração da conexão assíncrona com PostgreSQL usando SQLAlchemy 2.0
e asyncpg.

Este módulo é a BASE para todos os models SQLAlchemy. Ele fornece:

  1. `Base`         → classe base declarativa dos models
  2. `engine`       → engine assíncrona do PostgreSQL
  3. `AsyncSessionLocal` → fábrica de sessões assíncronas
  4. `get_db()`     → dependência FastAPI que fornece uma sessão
  5. `init_db()`    → cria todas as tabelas (para dev)
  6. `close_db()`   → fecha a conexão (shutdown)

ARQUITETURA DE DADOS — 3 BANCOS
───────────────────────────────
  ⚡ Redis       → cache quente (sessões, rate limit, filas)
  🍃 MongoDB     → persistência principal (conversas, contatos)
  🐘 PostgreSQL  → backup frio + dados relacionais (usuários, empresas)

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Este módulo é agnóstico de canal e segmento. Funciona igualmente em
WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em qualquer
segmento de negócio.

QUEM GERA
─────────
Arquivo CUSTOM (não é gerado automaticamente).

QUEM CONSOME
────────────
  • app/main.py         → inicializa a conexão
  • app/models/*        → importam `Base`
  • app/repositories/*  → recebem `AsyncSession` via DI
  • app/services/*      → usam repositórios

DEPENDÊNCIAS
────────────
  • sqlalchemy[asyncio]==2.0.30
  • asyncpg==0.29.0
  • pydantic-settings==2.2.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ═══════════════════════════════════════════════════════════════════════════
# CLASSE BASE DECLARATIVA
# ═══════════════════════════════════════════════════════════════════════════
# Todos os models SQLAlchemy herdam desta classe.
# Usa o padrão `DeclarativeBase` do SQLAlchemy 2.0 (moderno).


class Base(DeclarativeBase):
    """
    Classe base declarativa para todos os models SQLAlchemy do projeto.

    Uso nos models:
        from app.database import Base

        class Usuario(Base):
            __tablename__ = 'usuarios'
            id = Column(Integer, primary_key=True)
            ...

    Vantagens do DeclarativeBase (SQLAlchemy 2.0):
      • Tipagem estática melhor (mypy, pyright)
      • Sintaxe mais limpa (sem metaclass)
      • Compatível com `Mapped[]` e `mapped_column()`
    """
    pass


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE ASSÍNCRONA
# ═══════════════════════════════════════════════════════════════════════════
# A engine gerencia o pool de conexões com o PostgreSQL.
# Configurada para produção (pool_pre_ping, pool_recycle).


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,              # loga SQL em desenvolvimento
    future=True,                      # compatível com SQLAlchemy 2.0
    pool_pre_ping=True,               # testa conexão antes de usar
    pool_size=10,                     # conexões no pool
    max_overflow=20,                  # conexões extras além do pool
    pool_recycle=3600,                # recicla conexões após 1h
)


# ═══════════════════════════════════════════════════════════════════════════
# FÁBRICA DE SESSÕES
# ═══════════════════════════════════════════════════════════════════════════
# `async_sessionmaker` cria sessões assíncronas vinculadas à engine.
# `expire_on_commit=False` evita lazy loads após commit.


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,           # objetos ficam válidos após commit
    autoflush=False,                  # controle manual do flush
)


# ═══════════════════════════════════════════════════════════════════════════
# DEPENDÊNCIA FASTAPI — get_db()
# ═══════════════════════════════════════════════════════════════════════════
# Fornece uma sessão de banco por requisição HTTP, garantindo
# fechamento automático ao final.


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência FastAPI que fornece uma `AsyncSession` por requisição.

    Uso em routers:
        from fastapi import Depends
        from app.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession

        @router.get('/usuarios')
        async def listar(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO E SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════
# Chamados no startup/shutdown do FastAPI.


async def init_db() -> None:
    """
    Cria todas as tabelas definidas nos models.

    ⚠️ Só use em desenvolvimento. Em produção, use Alembic:
        alembic upgrade head
    """
    # Importa todos os models para que o `Base.metadata` os conheça
    from app.models import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fecha a engine e libera o pool de conexões."""
    await engine.dispose()