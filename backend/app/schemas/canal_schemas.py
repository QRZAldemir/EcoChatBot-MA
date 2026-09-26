"""
================================================================================
MÓDULO: app/schemas/canal_schemas.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 3.0.0
OBJETIVO: Schemas Pydantic do canal CONTRATADO — a unidade de canal do EcoChatBot.
PASTA: backend/app/schemas/
================================================================================

O QUE MUDOU NESTA VERSÃO (3.0.0)
-------------------------------
    Antes o schema era `Canal*` e o canal era um registro solto da empresa.
    Agora o canal é um ITEM DO CONTRATO: `CanalContratado`.

    • `telefone_id` passou a ser OBRIGATÓRIO. Todo canal é sustentado por um
      telefone. É por isso que a empresa pode ter vários WhatsApps: cada um
      fica amarrado a um telefone diferente.
    • `nome` virou `apelido` (apelido é o nomeAmigável; `tipo` é o tipo técnico).
    • `departamento_id` saiu: quem atende é o MENU (MenuItem.departamento_id),
      não o canal.
    • `identificador` e `configuracao` passaram a viver em `credenciais`, que é
      o JSON do canal. As VALIDAÇÕES por tipo foram preservadas — só mudou o
      lugar onde o valor é guardado.
    • A OFUSCAÇÃO de identificador na resposta foi preservada: é o que impede
      o token do Telegram de vazar em um log ou resposta de API.

REGRAS QUE VALEM PARA TODOS OS TIPOS
------------------------------------
    • 1 tipo por telefone — o banco garante com `uq_canais_contratados_telefone_tipo`
    • canal sem telefone → sistema recusa com 403
    • webhook só é aceito se o `webhook_token` da URL bater
================================================================================
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# ENUMS DE TIPOS DE CANAL
# ==============================================================================
# O model `CanalContratado.tipo` é String(20) livre — o tipo é uma ESCOLHA da
# empresa compradora, e o Literal é só a lista do que o front-known. Um tipo
# novo (ex.: "signal", "matrix") não exige migration: basta somar aqui.
TipoCanal = Literal[
    "whatsapp",
    "telegram",
    "instagram",
    "facebook",
    "discord",
    "pabx",
    "voip_telefonia",
    "email",
    "chat_web",
]

StatusCanal = Literal["ativo", "inativo", "pendente_configuracao", "erro_conexao"]

#: Chave usada dentro de `credenciais` para o identificador de cada tipo.
CHAVE_IDENTIFICADOR: Dict[str, str] = {
    "whatsapp": "phone_number",
    "telegram": "bot_token",
    "instagram": "page_id",
    "facebook": "page_id",
    "discord": "bot_token",
    "email": "endereco",
}


# ==============================================================================
# SCHEMAS DO CANAL CONTRATADO
# ==============================================================================
class CanalContratadoBase(BaseModel):
    """
    Campos comuns de criação e atualização de um canal contratado.

    `telefone_id` é obrigatório porque o canal é um ITEM DO CONTRATO amarrado
    a um telefone: é aconstraint que impede a empresa de ter dois WhatsApp no
    mesmo número e, ao mesmo tempo, permite ter vários em números diferentes.
    """

    tipo: TipoCanal = Field(
        ...,
        description="Tipo do canal de comunicação",
        examples=["whatsapp", "telegram", "pabx"],
    )
    telefone_id: int = Field(
        ...,
        description="Telefone que sustenta este canal — eixo da contratação",
        examples=[1, 2, 3],
    )
    apelido: Optional[str] = Field(
        None,
        min_length=3,
        max_length=80,
        description="Nome amigável do canal (ex: WhatsApp Comercial)",
        examples=["WhatsApp Comercial", "Telegram Suporte"],
    )
    credenciais: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Credenciais e identificador técnico do canal, em JSON. "
            "Ex.: {\"phone_number\": \"556734167800\"} ou "
            "{\"bot_token\": \"123456:ABC-DEF\"}"
        ),
    )
    webhook_token: Optional[str] = Field(
        None, max_length=120, description="Valida a origem do webhook recebido"
    )
    webhook_url: Optional[str] = Field(
        None, max_length=300, description="URL cadastrada no provedor (Meta, Telegram)"
    )
    horario_inicio: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}$", description="Expediente — início (ex: 08:00)"
    )
    horario_fim: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}$", description="Expediente — fim (ex: 18:00)"
    )
    dias_semana: Optional[str] = Field(
        None, max_length=20, description="Dias de atendimento, ex: 1,2,3,4,5"
    )
    ativo: bool = Field(True, description="Status de ativação do canal")

    @field_validator("horario_inicio", "horario_fim")
    @classmethod
    def validar_horario(cls, v: Optional[str]) -> Optional[str]:
        """Garante HH:MM dentro da faixa válida."""
        if v is None:
            return None
        hora, _, minuto = v.partition(":")
        if not (0 <= int(hora) <= 23 and 0 <= int(minuto) <= 59):
            raise ValueError(f"Horário inválido: {v}. Use o formato HH:MM")
        return v

    @field_validator("dias_semana")
    @classmethod
    def validar_dias(cls, v: Optional[str]) -> Optional[str]:
        """Garante que os dias são 1..7 (1=segunda ... 7=domingo)."""
        if v is None or not v.strip():
            return None
        dias = [int(d) for d in v.replace(" ", "").split(",") if d]
        fora = [d for d in dias if not 1 <= d <= 7]
        if fora:
            raise ValueError(f"Dia(s) inválido(s): {fora}. Use 1 a 7 (1=segunda)")
        return ",".join(str(d) for d in dias)


class CanalContratadoCreate(CanalContratadoBase):
    """
    Criação de canal contratado.

    `empresa_id` vem do contexto de autenticação (é o tenant). `identificador`
    é validado por tipo e guardado dentro de `credenciais` pelo service.
    """

    empresa_id: int = Field(..., description="Empresa que contrata o canal (tenant)")

    identificador: Optional[str] = Field(
        None,
        min_length=3,
        max_length=255,
        description=(
            "Identificador técnico do canal no provedor. Vira "
            "`credenciais[%s]`. WhatsApp: só dígitos (556734167800). "
            "Telegram: ID:HASH. Instagram/Facebook: page_id numérico."
        )
        % "phone_number | bot_token | page_id",
    )

    @field_validator("identificador")
    @classmethod
    def validar_identificador(cls, v: Optional[str], info) -> Optional[str]:
        """
        Valida o identificador de acordo com o tipo do canal.

        - WhatsApp: só dígitos, 10 a 13 (DDI + número)
        - Telegram:  ID:HASH
        - Instagram/Facebook: page_id numérico
        - email:      endereço com @
        """
        if v is None or not str(v).strip():
            return None
        tipo = info.data.get("tipo")
        v = str(v).strip()

        if tipo == "whatsapp":
            numeros = re.sub(r"\D", "", v)
            if not 10 <= len(numeros) <= 13:
                raise ValueError("Número WhatsApp inválido. Use formato: 556734167800")
            return numeros

        if tipo == "telegram":
            if not re.match(r"^\d+:[A-Za-z0-9_-]+$", v):
                raise ValueError("Token Telegram inválido. Formato esperado: ID:HASH")
            return v

        if tipo in ("instagram", "facebook"):
            if not v.isdigit():
                raise ValueError("Page ID deve conter apenas números")
            return v

        if tipo == "email":
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("Endereço de e-mail inválido")
            return v.lower()

        return v


class CanalContratadoUpdate(BaseModel):
    """Atualização parcial. Só o que for enviado muda."""

    tipo: Optional[TipoCanal] = None
    telefone_id: Optional[int] = None
    apelido: Optional[str] = Field(None, min_length=3, max_length=80)
    credenciais: Optional[Dict[str, Any]] = None
    webhook_token: Optional[str] = Field(None, max_length=120)
    webhook_url: Optional[str] = Field(None, max_length=300)
    horario_inicio: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    horario_fim: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    dias_semana: Optional[str] = Field(None, max_length=20)
    ativo: Optional[bool] = None

    _validar_horario = field_validator("horario_inicio", "horario_fim")(
        CanalContratadoBase.validar_horario.__func__
    )


def _ofuscar(valor: str) -> str:
    """5511999999999 → 5511****9999 | 123456:ABCDEF... → 1234****W11u"""
    if ":" in valor:
        inicio, _, resto = valor.partition(":")
        if len(resto) > 8:
            return f"{inicio}:{resto[:4]}****{resto[-4:]}"
    if len(valor) > 8:
        return f"{valor[:4]}****{valor[-4:]}"
    return valor


class CanalContratadoResponse(CanalContratadoBase):
    """Resposta de leitura. NUNCA devolve o identificador em claro."""

    id: int
    empresa_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    # Campo calculado: o identificador vem sempre ofuscado.
    identificador: Optional[str] = Field(
        None, description="Identificador do canal, ofuscado por segurança"
    )
    status_conexao: Optional[str] = Field(
        None, description="Status da conexão com a API externa"
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("credenciais", mode="after")
    @classmethod
    def ofuscar_credenciais(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Ofusca os segredos na RESPOSTA.

        O banco guarda o valor real (o serviço precisa dele para falar com o
        provedor), mas nada disso pode voltar para o navegador: nem o token do
        bot, nem o número do WhatsApp. Este é o ponto onde isso é garantido.
        """
        if not v:
            return v
        CHAVES_SENSIVEIS = {
            "bot_token", "access_token", "token", "api_secret",
            "auth_token", "account_sid", "password", "secret",
        }
        saida = {}
        for chave, valor in v.items():
            if chave in CHAVES_SENSIVEIS and isinstance(valor, str):
                saida[chave] = _ofuscar(valor)
            elif isinstance(valor, str) and re.fullmatch(r"\d{10,13}", valor):
                saida[chave] = _ofuscar(valor)
            else:
                saida[chave] = valor
        return saida


class CanalContratadoDetalhado(CanalContratadoResponse):
    """Canal contratado com métricas de atendimento."""

    total_atendimentos: int = Field(0, description="Total de atendimentos no canal")
    atendimentos_ativos: int = Field(0, description="Atendimentos em aberto agora")
    ultima_mensagem: Optional[datetime] = Field(
        None, description="Data da última mensagem recebida/enviada"
    )


class CanalListaResponse(BaseModel):
    """Listagem paginada de canais contratados."""

    total: int
    page: int
    limit: int
    total_pages: int
    canais: List[CanalContratadoResponse]


# ==============================================================================
# SCHEMAS ESPECÍFICOS POR TIPO DE CANAL
# ==============================================================================
class CanalWhatsAppConfig(BaseModel):
    """Configurações específicas para canal WhatsApp."""

    waba_id: Optional[str] = Field(None, description="WhatsApp Business Account ID")
    phone_number_id: Optional[str] = Field(None, description="Phone Number ID (Meta)")
    business_account_id: Optional[str] = Field(None, description="Business Account ID")
    template_namespace: Optional[str] = Field(None, description="Namespace de templates")
    usar_api_oficial: bool = Field(
        True, description="Usar Meta Cloud API (True) ou Evolution (False)"
    )


class CanalTelegramConfig(BaseModel):
    """Configurações específicas para canal Telegram."""

    bot_username: Optional[str] = Field(None, description="Username do bot (@meubot)")
    allowed_updates: List[str] = Field(
        default_factory=lambda: ["message", "callback_query"],
        description="Tipos de atualizações permitidas",
    )
    timeout: int = Field(30, description="Timeout em segundos para requests")


class CanalVoIPConfig(BaseModel):
    """Configurações específicas para canal VoIP/Telefonia/PABX."""

    pabx_type: str = Field(
        ..., description="asterisk_ari, 3cx, intelbras, generic_rest"
    )
    api_base_url: str = Field(..., description="URL da API do PABX")
    api_user: str = Field(..., description="Usuário da API do PABX")
    api_secret: str = Field(..., description="Senha ou Token da API do PABX")
    trunk_outbound: str = Field(
        ..., description="Tronco SIP para chamadas externas (ex: SIP/Vivo)"
    )
    context_ura: str = Field(
        default="eco_ura_entrada", description="Contexto do Dialplan para a URA do Bot"
    )
    stt_provider: str = Field(default="openai", description="Provedor de Speech-to-Text")
    tts_provider: str = Field(default="openai", description="Provedor de Text-to-Speech")


# ==============================================================================
# SCHEMAS DE WEBHOOK
# ==============================================================================
class WebhookVerifyRequest(BaseModel):
    """Verificação de webhook (Meta/Telegram)."""

    mode: str = Field(..., description="Mode de verificação")
    token: str = Field(..., description="Token de verificação")
    challenge: str = Field(..., description="Challenge para validação")


class WebhookMetaRequest(BaseModel):
    """Webhook da Meta (WhatsApp/Instagram/Facebook)."""

    object: str
    entry: List[Dict[str, Any]]


# ==============================================================================
# SCHEMAS DE MÉTRICAS
# ==============================================================================
class CanalMetricasResumo(BaseModel):
    """
    Resumo de métricas do canal para o dashboard.

    Os campos batem 1:1 com o dicionário devolvido por
    `CanalService.obter_metricas_canal` — se um mudar, o outro avisa.

    Repare que NÃO há "mensagens_enviadas/recebidas": as mensagens vivem no
    MongoDB e não são contadas aqui. O que existe é contagem de ATENDIMENTOS.
    """

    canal_id: int
    canal_apelido: Optional[str] = None
    tipo: str
    status: str
    atendimentos_hoje: int = 0
    atendimentos_ativos: int = 0
    atendimentos_com_atendente_hoje: int = 0
    tempo_medio_primeira_resposta_min: Optional[float] = None
    proximo: Optional[str] = Field(
        None, description="Observação sobre a origem destes números"
    )


# ==============================================================================
# COMPATIBILIDADE
# Os nomes `Canal*` apontam para `CanalContratado*`. ATENÇÃO: são aliases com a
# assinatura nova — `telefone_id` passou a ser obrigatório. Código que ainda
# usa `CanalCreate(nome=..., cliente_id=...)` vai falhar na validação, que é
# exatamente o sinal de que precisa migrar.
# ==============================================================================
CanalBase = CanalContratadoBase
CanalCreate = CanalContratadoCreate
CanalUpdate = CanalContratadoUpdate
CanalResponse = CanalContratadoResponse
CanalDetalhado = CanalContratadoDetalhado

__all__ = [
    "CanalContratadoBase", "CanalContratadoCreate", "CanalContratadoUpdate",
    "CanalContratadoResponse", "CanalContratadoDetalhado", "CanalListaResponse",
    "CanalWhatsAppConfig", "CanalTelegramConfig", "CanalVoIPConfig",
    "WebhookVerifyRequest", "WebhookMetaRequest", "CanalMetricasResumo",
    "TipoCanal", "StatusCanal", "CHAVE_IDENTIFICADOR",
    "CanalBase", "CanalCreate", "CanalUpdate", "CanalResponse", "CanalDetalhado",
]
