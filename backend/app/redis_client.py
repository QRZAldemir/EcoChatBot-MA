"""
================================================================================
MÓDULO: app/redis_client.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 1.0.0
OBJETIVO: Cliente Redis assíncrono único, compartilhado por toda a aplicação,
          usado como cache quente e como blacklist de tokens revogados.
PASTA: backend/app/
================================================================================
"""
import logging

from redis.asyncio import Redis, from_url

from app.config import settings

logger = logging.getLogger(__name__)

#: URL de conexão resolvida a partir de REDIS_URL no .env da raiz do projeto.
REDIS_URL: str = settings.redis_url

#: Cliente assíncrono compartilhado. `from_url` não abre socket na importação:
#: a conexão só é estabelecida no primeiro comando, e a falha aparece na
#: requisição com a causa original do Redis, não como erro de import quebrado.
redis_client: Redis = from_url(REDIS_URL, decode_responses=True)


def get_redis() -> Redis:
    """Retorna o cliente Redis compartilhado para uso como dependência FastAPI."""
    return redis_client


async def close_redis() -> None:
    """Encerra a conexão do cliente Redis. Usar no evento de shutdown da app."""
    await redis_client.aclose()
    logger.info("conexao redis encerrada")
