"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Configurações Globais (Fonte Única de Verdade)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     config.py
@module   Backend / App / Config
@author   Aldemir Queiroz
@since    2026
@version  2.1.0  · Path resolution robusto + validação cruzada Pydantic V2
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Centraliza e valida TODAS as variáveis de ambiente usando Pydantic V2.
Garante fail-fast na inicialização se uma config crítica estiver ausente.

DOMÍNIOS COBERTOS
─────────────────
    1. App         → nome, versão, ambiente
    2. Segurança   → JWT (chave, algoritmo, expiração)
    3. CORS        → origens permitidas
    4. PostgreSQL  → URL assíncrona (asyncpg)
    5. MongoDB     → URI + database
    6. Redis       → URI (cache + blacklist)
    7. IA          → DeepSeek (LLM)
    8. Canais      → WhatsApp, Telegram, Discord, Instagram, Facebook, PABX
    9. Acessibilidade → OCR (Tesseract) + TTS (gTTS/Edge-TTS)
    10. Logs       → nível + formato

USO
───
    from app.config import settings
    print(settings.app_name)
    print(settings.async_database_url)
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve o caminho absoluto para a raiz do projeto (3 níveis acima deste arquivo)
# backend/app/config.py -> backend/app -> backend -> raiz
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Configuração tipada da aplicação."""

    # ═══════════════════════════════════════════════════════════════════════
    # 1. CONFIGURAÇÕES GERAIS DA APLICAÇÃO
    # ═══════════════════════════════════════════════════════════════════════
    app_name: str = Field(default="EcoChat Marcx API", description="Nome da aplicação")
    app_version: str = Field(default="2.1.0", description="Versão atual da API")
    debug: bool = Field(default=False, description="Modo debug (docs + logs detalhados)")
    environment: str = Field(default="development", description="development | staging | production")

    # ═══════════════════════════════════════════════════════════════════════
    # 2. SEGURANÇA E AUTENTICAÇÃO (JWT)
    # ═══════════════════════════════════════════════════════════════════════
    secret_key: str = Field(
        default="",
        alias="JWT_SECRET",
        description="Chave secreta JWT. DEVE ser alterada em produção (≥32 chars).",
    )
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo de criptografia do JWT")
    jwt_expires_in: str = Field(default="8h", description="Validade do token (ex: '30m', '8h', '7d')")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. CORS (Cross-Origin Resource Sharing)
    # ═══════════════════════════════════════════════════════════════════════
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:4200", "http://localhost:3000"],
        description="Origens permitidas para CORS. No .env, separadas por vírgula.",
    )

    # ═══════════════════════════════════════════════════════════════════════
    # 4. POSTGRESQL (SQLAlchemy Async)
    # ═══════════════════════════════════════════════════════════════════════
    database_url: Optional[str] = Field(default=None, description="URL completa do banco. Prioritária se fornecida.")
    postgres_user: str = Field(default="ecochat", alias="POSTGRES_USER")
    postgres_password: str = Field(default="ecochat123", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="ecochat", alias="POSTGRES_DB")

    # ═══════════════════════════════════════════════════════════════════════
    # 5. MONGODB & 6. REDIS
    # ═══════════════════════════════════════════════════════════════════════
    mongo_url: str = Field(default="mongodb://localhost:27017", description="URI de conexão MongoDB")
    mongo_db_name: str = Field(default="ecochat", description="Nome do database MongoDB")
    redis_url: str = Field(default="redis://localhost:6379/0", description="URI de conexão Redis")

    # ═══════════════════════════════════════════════════════════════════════
    # 7. IA / LLM (DeepSeek)
    # ═══════════════════════════════════════════════════════════════════════
    ia_provider: str = Field(default="deepseek", description="Provedor de IA")
    ia_model: str = Field(default="deepseek-chat", description="Modelo LLM")
    deepseek_api_key: str = Field(default="", description="API key do DeepSeek")
    deepseek_api_url: str = Field(default="https://api.deepseek.com/v1", description="URL base do DeepSeek")

    # ═══════════════════════════════════════════════════════════════════════
    # 8. CANAIS DE ATENDIMENTO (Multi-canal)
    # ═══════════════════════════════════════════════════════════════════════
    whatsapp_enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")
    whatsapp_token: str = Field(default="", alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_id: str = Field(default="", alias="WHATSAPP_PHONE_NUMBER_ID")

    telegram_enabled: bool = Field(default=False, alias="TELEGRAM_ENABLED")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")

    discord_enabled: bool = Field(default=False, alias="DISCORD_ENABLED")
    discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")

    instagram_enabled: bool = Field(default=False, alias="INSTAGRAM_ENABLED")
    instagram_token: str = Field(default="", alias="INSTAGRAM_ACCESS_TOKEN")

    facebook_enabled: bool = Field(default=False, alias="FACEBOOK_ENABLED")
    facebook_token: str = Field(default="", alias="FACEBOOK_PAGE_ACCESS_TOKEN")

    pabx_enabled: bool = Field(default=False, alias="PABX_ENABLED")
    pabx_server: str = Field(default="", alias="PABX_SERVER")
    pabx_user: str = Field(default="", alias="PABX_USER")
    pabx_password: str = Field(default="", alias="PABX_PASSWORD")

    # ═══════════════════════════════════════════════════════════════════════
    # 9. ACESSIBILIDADE (OCR + TTS)
    # ═══════════════════════════════════════════════════════════════════════
    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    ocr_language: str = Field(default="por", alias="OCR_LANGUAGE")
    tts_enabled: bool = Field(default=True, alias="TTS_ENABLED")
    tts_language: str = Field(default="pt-BR", alias="TTS_LANGUAGE")

    # ═══════════════════════════════════════════════════════════════════════
    # 10. LOGS
    # ═══════════════════════════════════════════════════════════════════════
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # ═══════════════════════════════════════════════════════════════════════
    # CONFIGURAÇÃO DO PYDANTIC
    # ═══════════════════════════════════════════════════════════════════════
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,       # Caminho absoluto resolvido dinamicamente
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ═══════════════════════════════════════════════════════════════════════
    # VALIDADORES
    # ═══════════════════════════════════════════════════════════════════════
    @field_validator("secret_key")
    @classmethod
    def check_secret_key_length(cls, v: str) -> str:
        """Garante que a chave tenha tamanho mínimo de segurança."""
        if v and len(v) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres.")
        return v

    @model_validator(mode="after")
    def check_production_security(self) -> "Settings":
        """Validação cruzada: exige secret_key forte em produção."""
        if self.environment == "production":
            if not self.secret_key or self.secret_key == "super-secret-key-change-in-production":
                raise ValueError("SECRET_KEY deve ser definida e forte (≥32 chars) em ambiente de produção.")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Converte 'http://a, http://b' → ['http://a', 'http://b']."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIEDADES COMPUTADAS
    # ═══════════════════════════════════════════════════════════════════════
    @property
    def async_database_url(self) -> str:
        """URL do PostgreSQL para SQLAlchemy assíncrono (asyncpg)."""
        if self.database_url:
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def jwt_expire_timedelta(self) -> timedelta:
        """Converte '8h' / '30m' / '7d' em `timedelta`."""
        duration = self.jwt_expires_in.strip().lower()
        if not duration:
            return timedelta(hours=8)

        try:
            value = int(duration[:-1])
            unit = duration[-1]
            if unit == "d": return timedelta(days=value)
            if unit == "h": return timedelta(hours=value)
            if unit == "m": return timedelta(minutes=value)
            if unit == "s": return timedelta(seconds=value)
        except (ValueError, IndexError):
            pass

        return timedelta(hours=8)

    # Adicionar na classe Settings:

# Evolution API
evolution_api_base_url: str = Field(
    default="https://evolution-api.com",
    description="URL base da Evolution API",
)
evolution_api_key: str = Field(
    default="",
    description="API Key da Evolution API",
)


# ─── Instância global (singleton) ─────────────────────────────────────────
settings = Settings()

__all__ = ["Settings", "settings"]