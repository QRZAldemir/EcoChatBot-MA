"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Schemas do Canal (Pydantic v2)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canal_schemas.py
@module   Backend / App / Schemas / Canal
@author   Aldemir Queiroz
@since    2026
@version  4.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Validação de entrada/saída do recurso `Canal` (ponto de entrada de mensagens).

PONTOS DE ATENÇÃO
─────────────────
• `empresa_id` NUNCA aparece em Create/Update — vem do token (Anti-IDOR).
• `identificador` é campo "virtual" do Create: o service o converte em
  `credenciais[CHAVE_IDENTIFICADOR[tipo]]` antes de persistir.
• A resposta SEMPRE ofusca segredos (`bot_token`, `phone_number`, etc.).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ══════════════════════════════════════════════════════════════════════════
# ENUMS / LITERAIS
# ══════════════════════════════════════════════════════════════════════════
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

StatusCanal = Literal[
    "ativo",
    "inativo",
    "pendente_configuracao",
    "erro_conexao",
]

#: Chave usada dentro de `credenciais` para o identificador de cada tipo.
CHAVE_IDENTIFICADOR: Dict[str, str] = {
    "whatsapp":  "phone_number",
    "telegram":  "bot_token",
    "instagram": "page_id",
    "facebook":  "page_id",
    "discord":   "bot_token",
    "email":     "endereco",
    "pabx":      "ramal",
    "voip_telefonia": "ramal",
    "chat_web":  "widget_id",
}


# ══════════════════════════════════════════════════════════════════════════
# BASE
# ══════════════════════════════════════════════════════════════════════════
class CanalBase(BaseModel):
    """Campos comuns de criação e atualização."""

    tipo: TipoCanal = Field(..., description="Tipo do canal de comunicação")
    telefone_id: int = Field(
        ..., gt=0,
        description="Telefone que sustenta este canal (obrigatório)",
    )
    apelido: Optional[str] = Field(
        None, min_length=3, max_length=80,
        description='Nome amigável (ex.: "WhatsApp Comercial")',
    )
    credenciais: Optional[Dict[str, Any]] = Field(
        None,
        description="Credenciais em JSON. Preferir usar `identificador` no Create.",
    )
    webhook_token: Optional[str] = Field(None, max_length=120)
    webhook_url: Optional[str] = Field(None, max_length=300)
    horario_inicio: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    horario_fim: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    dias_semana: Optional[str] = Field(None, max_length=20)
    ativo: bool = Field(True)

    @field_validator("horario_inicio", "horario_fim")
    @classmethod
    def validar_horario(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        hora, _, minuto = v.partition(":")
        if not (0 <= int(hora) <= 23 and 0 <= int(minuto) <= 59):
            raise ValueError(f"Horário inválido: {v}. Use HH:MM.")
        return v

    @field_validator("dias_semana")
    @classmethod
    def validar_dias(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        dias = [int(d) for d in v.replace(" ", "").split(",") if d]
        fora = [d for d in dias if not 1 <= d <= 7]
        if fora:
            raise ValueError(f"Dia(s) inválido(s): {fora}. Use 1 a 7 (1=segunda).")
        return ",".join(str(d) for d in dias)


# ══════════════════════════════════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════════════════════════════════
class CanalCreate(CanalBase):
    """
    Payload de criação.

    🔒 `empresa_id` é PROIBIDO — `extra="forbid"` rejeita o request
       caso o cliente tente enviá-lo (defesa anti-IDOR na entrada).
    """

    identificador: Optional[str] = Field(
        None, min_length=3, max_length=255,
        description=(
            "Identificador técnico do canal no provedor. Vira "
            "`credenciais[CHAVE_IDENTIFICADOR[tipo]]`. "
            "WhatsApp: só dígitos. Telegram: ID:HASH. "
            "Instagram/Facebook: page_id numérico."
        ),
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("identificador")
    @classmethod
    def validar_identificador(
        cls, v: Optional[str], info,
    ) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        tipo = info.data.get("tipo")
        v = str(v).strip()

        if tipo == "whatsapp":
            numeros = re.sub(r"\D", "", v)
            if not 10 <= len(numeros) <= 13:
                raise ValueError("Número WhatsApp inválido. Ex.: 556734167800")
            return numeros

        if tipo in ("telegram", "discord"):
            if not re.match(r"^[A-Za-z0-9_:-]{3,}$", v):
                raise ValueError("Token inválido. Formato esperado: ID:HASH")
            return v

        if tipo in ("instagram", "facebook"):
            if not v.isdigit():
                raise ValueError("Page ID deve conter apenas números.")
            return v

        if tipo == "email":
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("Endereço de e-mail inválido.")
            return v.lower()

        return v


# ══════════════════════════════════════════════════════════════════════════
# UPDATE
# ══════════════════════════════════════════════════════════════════════════
class CanalUpdate(BaseModel):
    """Atualização parcial — só o que for enviado muda."""

    tipo: Optional[TipoCanal] = None
    telefone_id: Optional[int] = Field(None, gt=0)
    apelido: Optional[str] = Field(None, min_length=3, max_length=80)
    credenciais: Optional[Dict[str, Any]] = None
    webhook_token: Optional[str] = Field(None, max_length=120)
    webhook_url: Optional[str] = Field(None, max_length=300)
    horario_inicio: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    horario_fim: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    dias_semana: Optional[str] = Field(None, max_length=20)
    ativo: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("horario_inicio", "horario_fim")
    @classmethod
    def validar_horario(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        hora, _, minuto = v.partition(":")
        if not (0 <= int(hora) <= 23 and 0 <= int(minuto) <= 59):
            raise ValueError(f"Horário inválido: {v}. Use HH:MM.")
        return v


# ══════════════════════════════════════════════════════════════════════════
# RESPONSE
# ══════════════════════════════════════════════════════════════════════════
def _ofuscar(valor: str) -> str:
    """5511999999999 → 5511****9999 | 123456:ABCDEF → 1234****EF"""
    if ":" in valor:
        inicio, _, resto = valor.partition(":")
        if len(resto) > 8:
            return f"{inicio}:{resto[:4]}****{resto[-4:]}"
    if len(valor) > 8:
        return f"{valor[:4]}****{valor[-4:]}"
    return valor


class CanalResponse(CanalBase):
    """Resposta de leitura — NUNCA devolve o identificador em claro."""

    id: int
    empresa_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    identificador: Optional[str] = Field(
        None, description="Identificador do canal, ofuscado por segurança",
    )
    status_conexao: Optional[str] = Field(
        None, description="Status da conexão com a API externa",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("credenciais", mode="after")
    @classmethod
    def ofuscar_credenciais(
        cls, v: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
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


class CanalDetalhado(CanalResponse):
    """Canal com métricas."""

    total_atendimentos: int = Field(0)
    atendimentos_ativos: int = Field(0)
    ultima_mensagem: Optional[datetime] = None


class CanalListaResponse(BaseModel):
    """Listagem paginada."""

    total: int
    page: int
    limit: int
    total_pages: int
    canais: List[CanalResponse]


# ══════════════════════════════════════════════════════════════════════════
# CONFIG POR TIPO
# ══════════════════════════════════════════════════════════════════════════
class CanalWhatsAppConfig(BaseModel):
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    template_namespace: Optional[str] = None
    usar_api_oficial: bool = True


class CanalTelegramConfig(BaseModel):
    bot_username: Optional[str] = None
    allowed_updates: List[str] = Field(
        default_factory=lambda: ["message", "callback_query"]
    )
    timeout: int = 30


class CanalVoIPConfig(BaseModel):
    pabx_type: str
    api_base_url: str
    api_user: str
    api_secret: str
    trunk_outbound: str
    context_ura: str = "eco_ura_entrada"
    stt_provider: str = "openai"
    tts_provider: str = "openai"


# ══════════════════════════════════════════════════════════════════════════
# WEBHOOK
# ══════════════════════════════════════════════════════════════════════════
class WebhookVerifyRequest(BaseModel):
    mode: str
    token: str
    challenge: str


class WebhookMetaRequest(BaseModel):
    object: str
    entry: List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════
# MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════
class CanalMetricasResumo(BaseModel):
    canal_id: int
    canal_apelido: Optional[str] = None
    tipo: str
    status: str
    atendimentos_hoje: int = 0
    atendimentos_ativos: int = 0
    atendimentos_com_atendente_hoje: int = 0
    tempo_medio_primeira_resposta_min: Optional[float] = None
    proximo: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════
# ALIASES DE COMPATIBILIDADE (código antigo que ainda usa Canal*)
# ══════════════════════════════════════════════════════════════════════════
CanalContratadoBase = CanalBase
CanalContratadoCreate = CanalCreate
CanalContratadoUpdate = CanalUpdate
CanalContratadoResponse = CanalResponse
CanalContratadoDetalhado = CanalDetalhado


__all__ = [
    "TipoCanal", "StatusCanal", "CHAVE_IDENTIFICADOR",
    "CanalBase", "CanalCreate", "CanalUpdate",
    "CanalResponse", "CanalDetalhado", "CanalListaResponse",
    "CanalWhatsAppConfig", "CanalTelegramConfig", "CanalVoIPConfig",
    "WebhookVerifyRequest", "WebhookMetaRequest", "CanalMetricasResumo",
    # compat
    "CanalContratadoBase", "CanalContratadoCreate", "CanalContratadoUpdate",
    "CanalContratadoResponse", "CanalContratadoDetalhado",
]