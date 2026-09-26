"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · MongoDB Connection
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     mongodb.py
@module   Backend / App / Config
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Configuração da conexão assíncrona com MongoDB usando Motor
(driver oficial assíncrono do MongoDB para Python).

Este módulo é a BASE para todos os models MongoDB (Beanie ODM). Fornece:

  1. `client`          → cliente Motor assíncrono
  2. `db`              → referência ao banco de dados
  3. `get_database()`  → retorna a instância do banco
  4. `init_mongodb()`  → inicializa Beanie com os documentos
  5. `close_mongodb()` → fecha a conexão

ARQUITETURA DE DADOS — 3 BANCOS
───────────────────────────────
  ⚡ Redis       → cache quente (sessões, rate limit, filas)
  🍃 MongoDB     → persistência principal (conversas, contatos)
  🐘 PostgreSQL  → backup frio + dados relacionais (usuários, empresas)

RESPONSABILIDADE DO MONGODB
───────────────────────────
  • Conversas e histórico de mensagens
  • Contatos (clientes/pacientes/cidadãos)
  • Menus dinâmicos (estruturas JSON complexas)
  • Modelos de mensagem (templates)
  • Logs de IA / OCR
  • Webhooks recebidos
  • Configurações flexíveis por tenant

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Este módulo é agnóstico de canal e segmento. Funciona igualmente em
WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em qualquer
segmento de negócio (saúde, financeiro, varejo, educação, jurídico,
turismo, governo, serviços).

QUEM GERA
─────────
Arquivo CUSTOM (não é gerado automaticamente).

QUEM CONSOME
────────────
  • app/main.py         → inicializa a conexão
  • app/models_mongo/*  → documentos Beanie
  • app/services/*      → usam repositórios MongoDB

DEPENDÊNCIAS
────────────
  • motor==3.4.0
  • pymongo==4.7.2
  • beanie==1.26.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import logging
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL (singleton)
# ═══════════════════════════════════════════════════════════════════════════
# O cliente e o banco são inicializados UMA vez no startup do FastAPI
# e reutilizados durante toda a vida da aplicação.

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUÇÃO DA URL DE CONEXÃO
# ═══════════════════════════════════════════════════════════════════════════


def _build_mongo_url() -> str:
    """
    Monta a URL de conexão do MongoDB a partir das settings.

    Formato:
        mongodb://usuario:senha@host:porta/database?authSource=admin

    Returns:
        URL completa de conexão
    """
    return (
        f'mongodb://{settings.mongo_user}:{settings.mongo_password}'
        f'@{settings.mongo_host}:{settings.mongo_port}'
        f'/{settings.mongo_database}?authSource=admin'
    )


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


async def init_mongodb(document_models: list = None) -> AsyncIOMotorDatabase:
    """
    Inicializa a conexão com MongoDB e o Beanie ODM.

    Deve ser chamada no startup do FastAPI:

        from app.mongodb import init_mongodb
        from app.models_mongo import Conversa, Contato, Menu

        @app.on_event('startup')
        async def startup():
            await init_mongodb([Conversa, Contato, Menu])

    Args:
        document_models: lista de classes Beanie (Document) a registrar.
                         Se None, apenas a conexão é aberta.

    Returns:
        Instância do banco de dados MongoDB.
    """
    global _client, _database

    url = _build_mongo_url()
    logger.info(f'Conectando ao MongoDB em {settings.mongo_host}:{settings.mongo_port}')

    _client = AsyncIOMotorClient(url)
    _database = _client[settings.mongo_database]

    # Testa a conexão
    try:
        await _client.admin.command('ping')
        logger.info('✅ MongoDB conectado com sucesso')
    except Exception as e:
        logger.error(f'❌ Falha ao conectar no MongoDB: {e}')
        raise

    # Inicializa Beanie com os documentos registrados
    if document_models:
        await init_beanie(
            database=_database,
            document_models=document_models,
        )
        logger.info(f'✅ Beanie inicializado com {len(document_models)} documento(s)')

    return _database


# ═══════════════════════════════════════════════════════════════════════════
# ACESSO AO BANCO
# ═══════════════════════════════════════════════════════════════════════════


def get_database() -> AsyncIOMotorDatabase:
    """
    Retorna a instância do banco de dados MongoDB.

    Uso em serviços:
        from app.mongodb import get_database

        async def salvar_conversa(conversa: dict):
            db = get_database()
            await db.conversas.insert_one(conversa)

    Raises:
        RuntimeError: se o MongoDB não foi inicializado.

    Returns:
        Instância do banco de dados.
    """
    if _database is None:
        raise RuntimeError(
            'MongoDB não inicializado. '
            'Chame `init_mongodb()` no startup do FastAPI.'
        )
    return _database


def get_client() -> AsyncIOMotorClient:
    """
    Retorna o cliente Motor.

    Útil para operações administrativas (drop database, list collections).

    Raises:
        RuntimeError: se o MongoDB não foi inicializado.
    """
    if _client is None:
        raise RuntimeError(
            'MongoDB não inicializado. '
            'Chame `init_mongodb()` no startup do FastAPI.'
        )
    return _client


# ═══════════════════════════════════════════════════════════════════════════
# SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════


async def close_mongodb() -> None:
    """
    Fecha a conexão com MongoDB.

    Deve ser chamada no shutdown do FastAPI:

        @app.on_event('shutdown')
        async def shutdown():
            await close_mongodb()
    """
    global _client, _database

    if _client is not None:
        _client.close()
        _client = None
        _database = None
        logger.info('🔌 Conexão MongoDB fechada')


# ─── Alias de nome ────────────────────────────────────────────────────────────
# app/deps.py e app/routers/conexoes_routers.py importam `get_mongo_db`, mas a
# função deste módulo se chama `get_database`. É a mesma dependência: só o
# nome divergia.
get_mongo_db = get_database
