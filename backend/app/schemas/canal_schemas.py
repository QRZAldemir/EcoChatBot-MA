"""
================================================================================
MÓDULO: app/schemas/canal.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-16
VERSÃO: 2.0.0
OBJETIVO: Define os schemas Pydantic para validação e serialização de canais.
          Suporta todos os tipos de canais omnichannel com validação específica.
PASTA: backend/app/schemas/
================================================================================
"""
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


# ==============================================================================
# ENUMS DE TIPOS DE CANAL
# ==============================================================================
TipoCanal = Literal[
    "whatsapp",
    "telegram",
    "instagram",
    "facebook",
    "discord",
    "voip_telefonia",
    "email",
    "chat_web"
]

StatusCanal = Literal["ativo", "inativo", "pendente_configuracao", "erro_conexao"]
# backend/app/schemas/canal.py
from pydantic import BaseModel, Field

class CanalVoIPConfig(BaseModel):
    """Schema para validar o JSON de configuração de um Canal VoIP/PABX."""
    pabx_type: str = Field(..., description="asterisk_ari, 3cx, intelbras, generic_rest")
    api_base_url: str = Field(..., description="URL da API do PABX")
    api_user: str = Field(..., description="Usuário da API do PABX")
    api_secret: str = Field(..., description="Senha ou Token da API do PABX")
    trunk_outbound: str = Field(..., description="Tronco SIP para chamadas externas (ex: SIP/Vivo)")
    context_ura: str = Field(default="eco_ura_entrada", description="Contexto do Dialplan para a URA do Bot")
    stt_provider: str = Field(default="openai", description="Provedor de Speech-to-Text")
    tts_provider: str = Field(default="openai", description="Provedor de Text-to-Speech")

# ==============================================================================
# SCHEMAS BASE
# ==============================================================================
class CanalBase(BaseModel):
    """
    Schema base com campos comuns para criação e atualização de canais.
    
    Validações:
        - Nome: 3-100 caracteres, obrigatório
        - Tipo: deve ser um dos tipos suportados
        - Identificador: 3-255 caracteres, obrigatório
        - Configuração: JSON opcional com settings específicos
    """
    nome: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome amigável do canal (ex: WhatsApp Vendas)",
        examples=["WhatsApp Principal", "Telegram Suporte"]
    )
    descricao: Optional[str] = Field(
        None,
        max_length=300,
        description="Descrição detalhada do canal",
        examples=["Canal principal de vendas via WhatsApp"]
    )
    tipo: TipoCanal = Field(
        ...,
        description="Tipo do canal de comunicação",
        examples=["whatsapp", "telegram", "instagram"]
    )
    identificador: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Identificador técnico (token, número, page_id)",
        examples=["5511999999999", "123456:ABC-DEF1234ghIkl", "1234567890"]
    )
    configuracao: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON com configurações específicas do canal"
    )
    departamento_id: Optional[int] = Field(
        None,
        description="ID do departamento responsável",
        examples=[1, 2, 3]
    )
    ativo: bool = Field(
        True,
        description="Status de ativação do canal"
    )

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        """Valida e normaliza o nome do canal."""
        if not v or not v.strip():
            raise ValueError("Nome do canal não pode ser vazio")
        return v.strip()

    @field_validator("identificador")
    @classmethod
    def validar_identificador(cls, v: str, info) -> str:
        """
        Valida o identificador baseado no tipo de canal.
        
        Regras:
            - WhatsApp: deve ser número com DDI (ex: 5511999999999)
            - Telegram: deve ser token no formato ID:HASH
            - Instagram/Facebook: deve ser page_id numérico
        """
        tipo = info.data.get("tipo") if hasattr(info, "data") else None
        
        if tipo == "whatsapp":
            # Remove caracteres não numéricos
            numeros = re.sub(r"\D", "", v)
            if len(numeros) < 10 or len(numeros) > 13:
                raise ValueError(
                    "Número WhatsApp inválido. Use formato: 5511999999999"
                )
            return numeros
        
        elif tipo == "telegram":
            # Token Telegram: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
            if not re.match(r"^\d+:[A-Za-z0-9_-]+$", v):
                raise ValueError(
                    "Token Telegram inválido. Formato esperado: ID:HASH"
                )
            return v
        
        elif tipo in ("instagram", "facebook"):
            # Page ID deve ser numérico
            if not v.isdigit():
                raise ValueError("Page ID deve conter apenas números")
            return v
        
        return v


class CanalCreate(CanalBase):
    """
    Schema para criação de novo canal.
    
    Todos os campos são obrigatórios exceto descricao e configuracao.
    O cliente_id será injetado automaticamente via contexto de autenticação.
    """
    pass


class CanalUpdate(BaseModel):
    """
    Schema para atualização parcial de canal.
    
    Todos os campos são opcionais. Apenas campos fornecidos serão atualizados.
    """
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    descricao: Optional[str] = Field(None, max_length=300)
    identificador: Optional[str] = Field(None, min_length=3, max_length=255)
    configuracao: Optional[Dict[str, Any]] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None
    webhook_url: Optional[str] = Field(None, max_length=500)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: Optional[str]) -> Optional[str]:
        """Valida nome se fornecido."""
        if v is not None:
            if not v.strip():
                raise ValueError("Nome não pode ser vazio")
            return v.strip()
        return v


# ==============================================================================
# SCHEMAS DE RESPOSTA
# ==============================================================================
class CanalResponse(CanalBase):
    """
    Schema de resposta com dados completos do canal.
    
    Inclui:
        - ID do canal
        - ID do cliente (tenant)
        - URLs de webhook
        - Timestamps
        - Status de conexão
    """
    id: int
    cliente_id: int
    webhook_url: Optional[str] = None
    webhook_verify_token: Optional[str] = None
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    ultimo_sync: Optional[datetime] = None
    
    # Campo calculado
    status_conexao: Optional[str] = Field(
        None,
        description="Status da conexão com a API externa"
    )
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator("identificador", mode="after")
    @classmethod
    def ofuscar_identificador(cls, v: str, info) -> str:
        """
        Ofusca identificadores sensíveis na resposta.
        
        Regras:
            - Telegram: mostra apenas primeiros e últimos caracteres
            - WhatsApp: mostra apenas últimos 4 dígitos
            - Outros: ofusca parcialmente
        """
        data = info.data
        tipo = data.get("tipo")
        
        if tipo == "telegram" and ":" in v:
            # Token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
            partes = v.split(":")
            if len(partes) == 2:
                hash_part = partes[1]
                if len(hash_part) > 8:
                    ofuscado = f"{partes[0]}:{hash_part[:4]}****{hash_part[-4:]}"
                    return ofuscado
        
        elif tipo == "whatsapp":
            # WhatsApp: 5511999999999 → 5511****9999
            if len(v) >= 8:
                return f"{v[:4]}****{v[-4:]}"
        
        # Ofuscação genérica para outros tipos
        if len(v) > 8:
            return f"{v[:4]}****{v[-4:]}"
        
        return v


class CanalDetalhado(CanalResponse):
    """
    Schema com dados detalhados do canal incluindo métricas.
    """
    total_atendimentos: int = Field(
        0,
        description="Total de atendimentos neste canal"
    )
    atendimentos_ativos: int = Field(
        0,
        description="Atendimentos ativos no momento"
    )
    ultima_mensagem: Optional[datetime] = Field(
        None,
        description="Data da última mensagem recebida/enviada"
    )


class CanalListaResponse(BaseModel):
    """
    Schema para listagem paginada de canais.
    """
    total: int
    page: int
    limit: int
    total_pages: int
    canais: List[CanalResponse]


# ==============================================================================
# SCHEMAS ESPECÍFICOS POR TIPO DE CANAL
# ==============================================================================
class CanalWhatsAppConfig(BaseModel):
    """Configurações específicas para canal WhatsApp."""
    waba_id: Optional[str] = Field(None, description="WhatsApp Business Account ID")
    phone_number_id: Optional[str] = Field(None, description="Phone Number ID (Meta)")
    business_account_id: Optional[str] = Field(None, description="Business Account ID")
    template_namespace: Optional[str] = Field(None, description="Namespace de templates")
    usar_api_oficial: bool = Field(True, description="Usar Meta Cloud API (True) ou Evolution (False)")


class CanalTelegramConfig(BaseModel):
    """Configurações específicas para canal Telegram."""
    bot_username: Optional[str] = Field(None, description="Username do bot (@meubot)")
    allowed_updates: List[str] = Field(
        default_factory=lambda: ["message", "callback_query"],
        description="Tipos de atualizações permitidas"
    )
    timeout: int = Field(30, description="Timeout em segundos para requests")


class CanalVoIPConfig(BaseModel):
    """Configurações específicas para canal VoIP/Telefonia."""
    provider: Literal["twilio", "vonage", "zenvia", "totalvoice"] = Field(
        ...,
        description="Provedor de VoIP"
    )
    account_sid: Optional[str] = Field(None, description="Account SID (Twilio)")
    auth_token: Optional[str] = Field(None, description="Auth Token")
    phone_number: Optional[str] = Field(None, description="Número de telefone")
    stt_provider: str = Field("openai", description="Provedor de Speech-to-Text")
    tts_provider: str = Field("openai", description="Provedor de Text-to-Speech")


# ==============================================================================
# SCHEMAS DE WEBHOOK
# ==============================================================================
class WebhookVerifyRequest(BaseModel):
    """
    Schema para verificação de webhook (Meta/Telegram).
    """
    mode: str = Field(..., description="Mode de verificação")
    token: str = Field(..., description="Token de verificação")
    challenge: str = Field(..., description="Challenge para validação")


class WebhookMetaRequest(BaseModel):
    """
    Schema para webhook da Meta (WhatsApp/Instagram/Facebook).
    """
    object: str
    entry: List[Dict[str, Any]]


# ==============================================================================
# SCHEMAS DE MÉTRICAS
# ==============================================================================
class CanalMetricasResumo(BaseModel):
    """
    Resumo de métricas do canal para dashboard.
    """
    canal_id: int
    canal_nome: str
    tipo: str
    mensagens_enviadas_hoje: int
    mensagens_recebidas_hoje: int
    atendimentos_ativos: int
    tempo_medio_resposta_min: Optional[float]
    taxa_resposta_percent: Optional[float]