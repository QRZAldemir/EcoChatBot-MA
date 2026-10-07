"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Schemas de Conexão
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     conexao.py
@module   Backend / App / Schemas
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define os schemas Pydantic para requisições e respostas relacionadas
ao gerenciamento de conexões com canais (WhatsApp, Telegram, etc.).

REGRAS DE NEGÓCIO
─────────────────
    • StatusConexao reflete o estado real da sessão
    • QR Code só é válido por 60 segundos (padrão Evolution API)
    • Reconexão não deve deletar o registro, apenas renovar a sessão
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StatusConexaoEnum(str, Enum):
    """
    Estados possíveis de uma conexão com canal de mensagens.
    """
    DESCONECTADO = "desconectado"
    CONECTANDO = "conectando"
    CONECTADO = "conectado"
    AGUARDANDO_QRCODE = "aguardando_qrcode"
    ERRO = "erro"


class ConexaoStatusResponse(BaseModel):
    """
    Resposta do endpoint GET /conexoes/{id}/status
    """
    id: int = Field(..., description="ID da conexão")
    canal_contratado_id: int = Field(..., description="ID do canal contratado")
    status: StatusConexaoEnum = Field(..., description="Estado atual da conexão")
    mensagem: Optional[str] = Field(None, description="Mensagem descritiva do estado")
    iniciada_em: Optional[datetime] = Field(None, description="Data/hora de início da conexão")
    encerrada_em: Optional[datetime] = Field(None, description="Data/hora de término da conexão")
    tentativas: int = Field(default=1, description="Número de tentativas de conexão")
    
    # Informações adicionais da Evolution API
    qr_code: Optional[str] = Field(None, description="QR Code em base64 (se status=aguardando_qrcode)")
    instance_id: Optional[str] = Field(None, description="ID da instância na Evolution API")
    
    class Config:
        from_attributes = True


class ConexaoReconectarResponse(BaseModel):
    """
    Resposta do endpoint POST /conexoes/{id}/reconectar
    """
    mensagem: str = Field(..., description="Mensagem de confirmação")
    status: StatusConexaoEnum = Field(..., description="Novo estado da conexão")
    qr_code: Optional[str] = Field(None, description="QR Code (se aplicável)")
    reconectado_em: datetime = Field(default_factory=datetime.utcnow, description="Data/hora da reconexão")


class ConexaoCreate(BaseModel):
    """
    Schema para criação de nova conexão
    """
    canal_contratado_id: int = Field(..., description="ID do canal contratado")
    instance_name: str = Field(..., description="Nome da instância na Evolution API")
    webhook_url: Optional[str] = Field(None, description="URL do webhook")
    
    class Config:
        json_schema_extra = {
            "example": {
                "canal_contratado_id": 1,
                "instance_name": "whatsapp_empresa_x",
                "webhook_url": "https://api.empresa.com/webhook/whatsapp"
            }
        }


class ConexaoUpdate(BaseModel):
    """
    Schema para atualização de conexão
    """
    status: Optional[StatusConexaoEnum] = None
    mensagem: Optional[str] = None
    webhook_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "conectado",
                "mensagem": "Conexão estabelecida com sucesso"
            }
        }