# ==============================================================================
# app/security.py
# ──────────────────────────────────────────────────────────────────
# Emissão e verificação do JWT usado pelo painel administrativo.
#
# Antes só existia emissão (em routers/auth.py, só no /login) — nenhuma rota
# verificava o token de volta, então o backend aceitava qualquer requisição
# independente de haver ou não um usuário autenticado. `obter_usuario_atual`
# é a dependency que fecha essa lacuna: valida assinatura, expiração e se o
# token não foi revogado (logout), e é usada tanto por auth.py (/me,
# /refresh, /logout) quanto pelos routers administrativos protegidos em
# main.py.
#
# Variáveis de ambiente:
#     SECRET_KEY          Chave usada para assinar o JWT (obrigatória)
#     JWT_ALGORITHM       Algoritmo de assinatura (padrão: HS256)
#     JWT_EXPIRE_MINUTES  Validade do token em minutos (padrão: 480 = 8h)
# ==============================================================================

# ==============================================================================
# app/security.py
# Central de Segurança: Hash, JWT, Blacklist (Redis) e RBAC
# ==============================================================================
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Security (JWT + RBAC)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     security.py
@module   Backend / App / Security
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Centraliza TODA a lógica de SEGURANÇA do EcoChatBot-Marcx:

    1. Hash de senha (bcrypt)
    2. Verificação de senha
    3. Geração de JWT (access token)
    4. Decodificação e validação de JWT
    5. Hierarquia de níveis de acesso (RBAC)
    6. Blacklist de tokens revogados (via Redis)

RESPONSABILIDADES
─────────────────
    • `hash_senha()`              → hash bcrypt de senha
    • `verificar_senha()`         → valida senha contra hash
    • `criar_access_token()`      → gera JWT
    • `decodificar_token()`       → valida e decodifica JWT
    • `revogar_token()`           → adiciona JWT à blacklist
    • `token_esta_revogado()`     → verifica se JWT está na blacklist
    • `tem_nivel_minimo()`        → compara níveis (RBAC)
    • `ordem_nivel()`             → retorna índice do nível

HIERARQUIA DE NÍVEIS (RBAC)
───────────────────────────
    atendente (0) < supervisor (1) < gerente (2) < administrador (3)

RELACIONAMENTO COM OUTROS OBJETOS DO PROJETO
────────────────────────────────────────────
    security.py (este arquivo)
        │
        ├──► app/deps.py
        │      • `get_current_user()` usa `decodificar_token()`
        │      • `require_nivel()` usa `tem_nivel_minimo()`
        │
        ├──► app/services/auth_service.py
        │      • Login: `verificar_senha()` + `criar_access_token()`
        │      • Logout: `revogar_token()`
        │
        ├──► app/services/usuario_service.py
        │      • Criar usuário: `hash_senha()`
        │      • Trocar senha: `hash_senha()` + `verificar_senha()`
        │
        ├──► app/routers/*.py
        │      • `Depends(require_admin)` usa `tem_nivel_minimo()`
        │
        ├──► app/redis_client.py
        │      • Blacklist de JWT armazenada no Redis
        │
        ├──► app/exceptions/auth_exceptions.py
        │      • `TokenExpiradoException`, `TokenInvalidoException`
        │      • `TokenRevogadoException`, `NivelInsuficienteException`
        │
        └──► app/config.py
               • `jwt_secret`, `jwt_algorithm`, `jwt_expires_in`

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Agnóstico de canal e segmento.

USO
───
    from app.security import hash_senha, verificar_senha, criar_access_token

    # Criar senha
    hash = hash_senha('MinhaSenha123')

    # Login
    if verificar_senha('MinhaSenha123', user.senha_hash):
        token = criar_access_token(user_id=user.id, empresa_id=user.empresa_id)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

import anyio
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings  # Assume-se o uso de pydantic-settings
from app.database import get_async_session
from app.redis_client import redis_client
from app.models import Usuario, Nivel
from app.exceptions import (
    NaoAutenticadoException,
    TokenExpiradoException,
    TokenInvalidoException,
    TokenRevogadoException,
    NivelInsuficienteException,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÕES E CONTEXTOS
# ═══════════════════════════════════════════════════════════════════════════

# HTTPBearer é preferível ao OAuth2PasswordBearer para APIs REST modernas
_bearer_scheme = HTTPBearer(auto_error=False)

# Contexto de Hash (bcrypt é CPU-intensivo, será executado em thread separada)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hierarquia de Acesso (Índice maior = maior privilégio)
NIVEIS_HIERARQUIA: list[str] = ["atendente", "supervisor", "gerente", "administrador"]


# ═══════════════════════════════════════════════════════════════════════════
# 2. HASH DE SENHAS (NÃO-BLOQUEANTE)
# ═══════════════════════════════════════════════════════════════════════════

async def hash_senha(senha: str) -> str:
    """Gera hash bcrypt sem bloquear a event loop do FastAPI."""
    return await anyio.to_thread.run_sync(_pwd_context.hash, senha)

async def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Valida senha contra hash sem bloquear a event loop."""
    try:
        return await anyio.to_thread.run_sync(_pwd_context.verify, senha, hash_senha)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# 3. JWT: EMISSÃO E DECODIFICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def criar_access_token(user_id: int, empresa_id: int, nivel: str) -> str:
    """
    Gera um JWT assinado.
    Retorna o token string. O JTI (ID do token) é gerado para permitir revogação.
    """
    agora = datetime.now(timezone.utc)
    expiracao = agora + settings.jwt_expire_timedelta  # Ex: timedelta(hours=8)
    
    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,  # Identificador único para Blacklist
        "empresa_id": empresa_id, # Multi-tenant
        "nivel": nivel,
        "iat": agora,
        "exp": expiracao,
        "iss": "ecochatbot-marcx",
        "aud": "ecochatbot-frontend",
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict[str, Any]:
    """Valida assinatura, expiração e claims (aud/iss)."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="ecochatbot-frontend",
            issuer="ecochatbot-marcx",
        )
    except JWTError as e:
        logger.warning(f"security | Falha na decodificação JWT: {str(e)}")
        if "expired" in str(e).lower():
            raise TokenExpiradoException()
        raise TokenInvalidoException(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 4. BLACKLIST DE TOKENS (REDIS)
# ═══════════════════════════════════════════════════════════════════════════

async def revogar_token(jti: str, exp_timestamp: int) -> None:
    """
    Adiciona o token à blacklist no Redis.
    O TTL é calculado para que a chave seja apagada automaticamente 
    quando o token expirar naturalmente, evitando inchaço do Redis.
    """
    ttl = exp_timestamp - int(datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await redis_client.setex(f"revoked_token:{jti}", ttl, "1")

async def token_esta_revogado(jti: str) -> bool:
    """Verifica em O(1) se o token foi invalidado (logout)."""
    return bool(await redis_client.exists(f"revoked_token:{jti}"))


# ═══════════════════════════════════════════════════════════════════════════
# 5. FASTAPI DEPENDENCIES (GUARDIÕES)
# ═══════════════════════════════════════════════════════════════════════════

async def obter_usuario_atual(
    credenciais: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Usuario:
    """
    Dependency principal: Valida Token -> Checa Blacklist -> Busca Usuário Ativo.
    """
    if not credenciais:
        raise NaoAutenticadoException()

    # 1. Validação criptográfica e de expiração
    payload = decodificar_token(credenciais.credentials)
    jti = payload.get("jti")
    usuario_id = payload.get("sub")

    if not jti or not usuario_id:
        raise TokenInvalidoException("Payload do token malformado.")

    # 2. Verificação de Revogação (Logout) via Redis
    if await token_esta_revogado(jti):
        logger.info(f"security | Token revogado tentou acesso | jti={jti}")
        raise TokenRevogadoException()

    # 3. Busca do Usuário no Banco (Assíncrono)
    query = (
        select(Usuario)
        .options(selectinload(Usuario.nivel))
        .where(Usuario.id == int(usuario_id))
    )
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()

    if not usuario or not usuario.ativo:
        logger.warning(f"security | Acesso negado | user_id={usuario_id} | motivo=inativo/inexistente")
        raise NaoAutenticadoException()

    return usuario


# ═══════════════════════════════════════════════════════════════════════════
# 6. RBAC (CONTROLE DE ACESSO BASEADO EM PAPÉIS)
# ═══════════════════════════════════════════════════════════════════════════

def ordem_nivel(nivel: Optional[str]) -> int:
    """Retorna o índice hierárquico do nível (-1 se desconhecido)."""
    if not nivel:
        return -1
    try:
        return NIVEIS_HIERARQUIA.index(nivel.strip().lower())
    except ValueError:
        return -1

def tem_nivel_minimo(nivel_usuario: Optional[str], nivel_minimo: str) -> bool:
    """Verifica se o nível do usuário atende ao mínimo exigido."""
    return ordem_nivel(nivel_usuario) >= ordem_nivel(nivel_minimo)

def exigir_nivel(*niveis_permitidos: str):
    """
    Dependency para validação exata de níveis.
    Uso: @router.get("/", dependencies=[Depends(exigir_nivel("gerente", "administrador"))])
    """
    async def _verificador(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        if usuario.nivel and usuario.nivel.nome.lower() not in [n.lower() for n in niveis_permitidos]:
            raise NivelInsuficienteException()
        return usuario
    return _verificador

def exigir_nivel_minimo(nivel_minimo: str):
    """
    Dependency para validação hierárquica (ex: 'gerente' aceita 'administrador').
    Uso: @router.get("/", dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
    """
    if nivel_minimo.lower() not in NIVEIS_HIERARQUIA:
        raise ValueError(f"Nível de acesso desconhecido: {nivel_minimo}")

    async def _verificador(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        if not tem_nivel_minimo(usuario.nivel.nome if usuario.nivel else "", nivel_minimo):
            raise NivelInsuficienteException()
        return usuario
    return _verificador