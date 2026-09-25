"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · MongoDB Connection
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     mongodb.py
@module   Backend / App / Database
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Configura a conexão ASSÍNCRONA com MongoDB usando Motor (driver
oficial assíncrono) e Beanie (ODM baseado em Pydantic).

Este módulo fornece:
    • `client`           → cliente Motor
    • `db`               → referência ao banco
    • `get_database()`   → retorna instância do banco
    • `init_mongodb()`   → inicializa + registra Beanie documents
    • `close_mongodb()`  → fecha conexão

ARQUITETURA DE DADOS — 3 BANCOS
───────────────────────────────
    🐘 PostgreSQL → dados relacionais (usuários, empresas)
    🍃 MongoDB    → ESTE — dados flexíveis (conversas, contatos)
    ⚡ Redis      → dados efêmeros (sessões, cache)

RESPONSABILIDADE DO MONGODB
───────────────────────────
    • Conversas e histórico de mensagens
    • Contatos (clientes/pacientes/cidadãos)
    • Menus dinâmicos (estruturas JSON)
    • Modelos de mensagem (templates)
    • Logs de IA / OCR
    • Webhooks recebidos
    • Configurações flexíveis por tenant

RELACIONAMENTO COM OUTROS OBJETOS DO PROJETO
────────────────────────────────────────────
    mongodb.py (este arquivo)
        │
        ├──► app/models_mongo/*.py    (Beanie Documents)
        │      • Conversa, Contato, Menu, Mensagem, LogIA
        │
        ├──► app/services/*.py
        │      • ConversaService usa `get_database()`
        │      • ContatoService usa `get_database()`
        │      • MenuService usa `get_database()`
        │
        ├──► app/jobs/backup.py
        │      • Job Celery que lê MongoDB → escreve PostgreSQL
        │
        └──► main.py
               • Chama `init_mongodb()` no startup
               • Chama `close_mongodb()` no shutdown

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Agnóstico de canal e segmento.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import logging
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Estado global (singleton) ────────────────────────────────────────────
_client:   Optional[AsyncIOMotorClient]     = None
_database: Optional[AsyncIOMotorDatabase]   = None


def _build_mongo_url() -> str:
    """Monta a URL de conexão do MongoDB."""
    return (
        f'mongodb://{settings.mongo_user}:{settings.mongo_password}'
        f'@{settings.mongo_host}:{settings.mongo_port}'
        f'/{settings.mongo_database}?authSource=admin'
    )


async def init_mongodb(document_models: list = None) -> AsyncIOMotorDatabase:
    """
    Inicializa a conexão com MongoDB + Beanie ODM.

    Deve ser chamada no startup do FastAPI:

        from app.mongodb import init_mongodb
        from app.models_mongo import Conversa, Contato, Menu

        @app.on_event('startup')
        async def startup():
            await init_mongodb([Conversa, Contato, Menu])
    """
    global _client, _database

    url = _build_mongo_url()
    logger.info(f'Conectando ao MongoDB em {settings.mongo_host}:{settings.mongo_port}')

    _client = AsyncIOMotorClient(url)
    _database = _client[settings.mongo_database]

    try:
        await _client.admin.command('ping')
        logger.info('✅ MongoDB conectado')
    except Exception as e:
        logger.error(f'❌ Falha ao conectar no MongoDB: {e}')
        raise

    if document_models:
        await init_beanie(database=_database, document_models=document_models)
        logger.info(f'✅ Beanie inicializado com {len(document_models)} documento(s)')

    return _database


def get_database() -> AsyncIOMotorDatabase:
    """Retorna a instância do banco MongoDB."""
    if _database is None:
        raise RuntimeError('MongoDB não inicializado. Chame `init_mongodb()` no startup.')
    return _database


def get_client() -> AsyncIOMotorClient:
    """Retorna o cliente Motor."""
    if _client is None:
        raise RuntimeError('MongoDB não inicializado. Chame `init_mongodb()` no startup.')
    return _client


async def close_mongodb() -> None:
    """Fecha a conexão com MongoDB."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None
        logger.info('🔌 Conexão MongoDB fechada')


__all__ = [
    'init_mongodb',
    'get_database',
    'get_client',
    'close_mongodb',
]