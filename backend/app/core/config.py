# backend/app/core/config.py
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Configurações Centrais
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Config Façade
Codinome: EcoChatBot-MA
────────────────────────────────────────────────────────────────────────────
@file     config.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FUNCIONALIDADE
──────────────
Este arquivo concentra TODAS as configurações do sistema:
    • Configurações do SQLAlchemy (banco de dados)
    • Configurações de segurança (JWT, senhas)
    • Configurações de integrações (Discord, WhatsApp, etc.)
    • Configurações de serviços (e-mail, arquivos, etc.)

IMPORTANTE
────────────
    • Todas as configurações são carregadas via pydantic
    • Validação automática de tipos e valores
    • Suporte a variáveis de ambiente (.env)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@version  1.1.0
────────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Façade que reexporta `Settings` e `settings` a partir de `app.config`.

Por que este façade existe?
• Convenção de projeto: módulos de "core" ficam em `app.core.*`.
• Evita quebrar os 37+ módulos que já importam de `app.core.config`.
• Permite refatorar `app/config.py` no futuro sem impacto nos consumidores.

REGRAS DE NEGÓCIO
─────────────────
• NUNCA adicione lógica, classes ou validações aqui.
• A fonte única de verdade é `app.config`.
"""

from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # ─── Identidade do tenant ────────────────────────────────────────────
    # Uma empresa, um nome. O software e multi-tenant: estes valores sao
    # sobrescritos por tenant em tempo de negocio, e valem o padrao.
    APP_NAME: str = "EcoChatBot-MA"
    EMPRESA_NOME: str = "EcoChatBot-MA"
    EMPRESA_RODAPE: str = "EcoChatBot-MA"

    # Conteudo do bot. Vazio = o proprio servico monta o texto padrao.
    BOT_MENSAGEM_BOAS_VINDAS: str = ""
    LGPD_URL: str = ""

    # Configurações do Banco de Dados
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "echobot"
    
    # Configurações de Segurança
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configurações de Integrações
    DISCORD_BOT_TOKEN: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None

    # ─── Provedores de mensagem ──────────────────────────────────────────
    # Consumidos pelos adaptadores em app/adapters/providers/. Cada
    # adaptador lê o seu próprio par; o BotService só precisa de
    # BACKEND_URL, para montar a URL pública de um áudio gerado.

    # Evolution API (WhatsApp) — self-hosted ou EvoAI Cloud
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    # "apikey" (self-hosted) ou "api_access_token" (EvoAI Cloud)
    EVOLUTION_AUTH_HEADER: str = "apikey"

    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Meta Cloud API (WhatsApp Business Cloud)
    META_PHONE_NUMBER_ID: Optional[str] = None
    META_ACCESS_TOKEN: Optional[str] = None

    # PABX / VoIP
    PABX_API_URL: Optional[str] = None
    PABX_API_KEY: Optional[str] = None
    PABX_AUTH_TYPE: str = "bearer"  # "bearer" | "apikey"

    # URL pública do backend — usada para servir áudio gerado ao cliente
    BACKEND_URL: str = "http://localhost:8000"
    
    # Configurações de Serviços
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # Configurações de Arquivos
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância global das configurações
settings = Settings()
import logging
from typing import TYPE_CHECKING

# =======================================================================# VALIDAÇÃO DE DEPENDÊNCIA (Fail-Fast)
# =======================================================================try:
    from app.config import Settings as _Settings
    from app.config import settings as _settings
except ImportError as exc:
    raise ImportError(
        "Falha crítica: Não foi possível importar Settings de app.config. "
        "Verifique se o arquivo backend/app/config.py existe e está válido. "
        f"Erro original: {exc}"
    ) from exc

# =======================================================================# TYPE HINTS PARA IDEs (Autocomplete)
# =======================================================================if TYPE_CHECKING:
    from app.config import Settings as SettingsType
    from app.config import settings as settingsType

# =======================================================================# REEXPORTAÇÃO PÚBLICA
# =======================================================================Settings: type = _Settings
settings: object = _settings

__all__ = ["Settings", "settings"]

# =======================================================================# LOG DE INICIALIZAÇÃO
# =======================================================================_logger = logging.getLogger(__name__)
_logger.debug(
    "app.core.config carregado (façade) | environment=%s",
    getattr(_settings, "environment", "desconhecido"),
)