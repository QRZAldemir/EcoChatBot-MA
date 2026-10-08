"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Database Configuration
@file database.py
@author Aldemir Queiroz
@since 2026
@version 4.0.0 · Refatoração para SQLAlchemy Assíncrono (AsyncIO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Funcionalidade: Configuração do motor de banco de dados (Engine) e da fábrica de sessões (Session Maker) utilizando drivers assíncronos. Fornece a dependência injetável para os routers.
Relacionamento: É a base de toda a camada de dados. Todos os serviços (como o BotService) e routers dependem da sessão gerada por este arquivo para executar queries sem bloquear o Event Loop.
Autor: Aldemir Queiroz
__________________________________________________________________________
"""
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# IMPORTANTE: A URL do banco deve usar um driver assíncrono.
# Exemplo para PostgreSQL: "postgresql+asyncpg://user:password@host:port/dbname"
# Exemplo para SQLite (apenas dev): "sqlite+aiosqlite:///./ecochatbot.db"
from app.core.config import settings 

Base = declarative_base()

# Criação do Engine Assíncrono. 
# future=True garante compatibilidade com SQLAlchemy 2.0.
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG, # Log das queries em ambiente de desenvolvimento
    future=True,
    pool_pre_ping=True # Verifica conexões mortas antes de usar
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,       # Força o uso da classe assíncrona
    expire_on_commit=False,    # Evita erros de acesso a atributos após o commit
    autoflush=False,           # Controle manual do flush para melhor performance
)

async def get_async_db() -> AsyncIterator[AsyncSession]:
    """
    Dependência do FastAPI (Depends) para injetar a AsyncSession nas rotas.
    Garante que a sessão seja aberta, utilizada, comitada (se não houver erro) 
    e fechada corretamente ao final da requisição HTTP.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() #  Commit assíncrono ao final da requisição bem-sucedida
        except Exception:
            await session.rollback() #  Rollback assíncrono em caso de falha
            raise
        finally:
            await session.close() #  Liberação da conexão de volta ao pool