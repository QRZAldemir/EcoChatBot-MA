# -*- coding: utf-8 -*-
"""
Aldemir Queiroz da Silva
Data de Criação: 2023-11-20
Descrição: Serviços para operações de webhook
Funcionalidade: Implementa a lógica de negócio para operações de webhook
Classes Relacionadas:
    - Utiliza app/models_mongo/webhook_logs.py para acesso a dados
    - Conecta com app/routers/webhook_routers.py para endpoints
    - Pode ser utilizado por outros serviços para registro de logs
"""

from app.models_mongo.webhook_logs import WebhookLog
from app.mongodb import get_mongo

class WebhookLogService:
    """
    Serviço para gerenciar logs de webhooks
    Responsável por salvar e consultar logs de webhooks no MongoDB
    """
    
    async def save_log(self, canal: str, msg_id: str, payload: dict):
        """
        Salva um novo log de webhook
        Args:
            canal: Canal de origem do webhook
            msg_id: ID da mensagem original
            payload: Payload bruto recebido
        """
        log = WebhookLog(
            canal=canal,
            msg_id=msg_id,
            payload=payload
        )
        await log.insert()
    
    async def get_logs(self, canal: Optional[str] = None, processado: Optional[bool] = None):
        """
        Busca logs de webhook com filtros opcionais
        Args:
            canal: Filtrar por canal de origem
            processado: Filtrar por status de processamento
        Returns:
            List[WebhookLog]: Lista de logs encontrados
        """
        query = {}
        if canal:
            query["canal"] = canal
        if processado is not None:
            query["processado"] = processado
        
        return await WebhookLog.find(query).to_list()
