# backend/app/services/aps_service.py
import os
import redis
from typing import Optional, Dict
import json
import logging

logger = logging.getLogger(__name__)

class APSService:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        logger.info("APSService initialized successfully")
    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.error(f"Error getting key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: str, expire: int = None):
        try:
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Error setting key {key}: {str(e)}")
