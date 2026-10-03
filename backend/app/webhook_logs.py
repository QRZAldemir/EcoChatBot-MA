# -*- coding: utf-8 -*-
"""
Aldemir Queiroz da Silva
Data de Criação: 2023-11-20
Descrição: Modelos de dados para MongoDB
Funcionalidade: Define a estrutura dos documentos armazenados no MongoDB
Classes Relacionadas:
    - Utiliza beanie para mapeamento ORM
    - Conecta com app/mongodb.py para operações de banco
    - Utilizado por app/services/webhook_log_service.py para operações de serviço
"""

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from app.mongodb import get_mongo

class WebhookLog(Document):
    """
    Modelo para armazenamento de logs de webhooks
    Armazena payloads brutos de webhooks para auditoria e depuração
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    canal: str = Field(description="Canal de origem do webhook")
    msg_id: str = Field(description="ID da mensagem original")
    payload: dict = Field(description="Payload bruto recebido")
    processado: bool = Field(default=False, description="Indica se o webhook foi processado")
    erro: Optional[str] = Field(default=None, description="Erros ocorridos durante processamento")

    class Settings:
        name = "webhook_logs"
        database = get_mongo()
