"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: services/webhook_service.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Processar webhooks de entrada omnichannel. Utiliza Redis Assíncrono para 
deduplicação de eventos (evitando processamento duplo de mensagens), 
substituindo a checagem em memória local por chaves temporizadas (TTL 120s).

ARQUITETURA E INTEGRAÇÃO:
Camada de Serviço. Consome `redis.asyncio`. Integra-se aos handlers de 
bot e ao gateway PABX para roteamento de mensagens.
================================================================================
"""
import redis.asyncio as redis
from app.core.config import settings

class WebhookService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_duplicated(self, canal: str, msg_id: str) -> bool:
        key = f"webhook:dedup:{canal}:{msg_id}"
        # SET NX com TTL de 120 segundos
        is_new = await self.redis.set(key, "1", ex=120, nx=True)
        return is_new is None  # Se for None, a chave já existia (é duplicada)