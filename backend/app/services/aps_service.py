"""
app/services/aps_service.py
──────────────────────────────────────────────────────────────────
Serviço de cache/estado em Redis (assíncrono).
Variáveis de ambiente:
REDIS_HOST  Host do servidor Redis (padrão: localhost)
REDIS_PORT  Porta do Redis (padrão: 6379)
REDIS_DB    Número do banco de dados Redis (padrão: 0)
"""
import logging
import os
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class APSService:
    def __init__(self):
        self.client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )
        logger.info("APSService initialized successfully (async Redis client)")

    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.error("aps_service | get | erro ao buscar chave %s: %s", key, str(e))
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        try:
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error("aps_service | set | erro ao definir chave %s: %s", key, str(e))