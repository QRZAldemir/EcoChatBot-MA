# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.core.security
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-27
# VERSÃO: 2.0.0 (Consolidação: JWT + RBAC + Hash + Blacklist)
# ==============================================================================
"""
FUNCIONALIDADE
--------------
Central ÚNICA de Segurança do EcoChatBot-MA. 
Combina autenticação (JWT), autorização (RBAC), criptografia (bcrypt) e 
revogação de tokens (Redis blacklist) em um único módulo coeso.

RESPONSABILIDADES
-----------------
1. Hash de senha (bcrypt, não-bloqueante via anyio)
2. Verificação de senha
3. Geração de JWT (access token) com claims multi-tenant
4. Decodificação e validação de JWT
5. Blacklist de tokens revogados (Redis com TTL automático)
6. Hierarquia de níveis de acesso (RBAC)
7. Dependencies do FastAPI para proteção de rotas

HIERARQUIA DE NÍVEIS (RBAC)
----------------------------
atendente (0) < supervisor (1) < gerente (2) < administrador (3)

RELACIONAMENTOS
---------------
    app.core.security (este arquivo)
        │
        ├──► app/deps.py (re-exporta dependencies)
        ├──► app/services/auth_service.py (login/logout)
        ├──► app/services/usuario_service.py (criação/troca de senha)
        ├──► app/routers/*.py (proteção de endpoints)
        └──► app/redis_client.py (armazenamento de blacklist)

REGRAS DE NEGÓCIO
-----------------
• bcrypt com deprecated="auto": hashes antigos são aceitos e re-criptografados
• JWT com JTI (JWT ID) único para permitir revogação granular
• Blacklist com TTL calculado para auto-limpeza quando token expira
• Nunca logar senhas em texto puro ou tokens completos
• Exceções de segurança não revelam se o usuário existe (timing-safe)
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

from app.config import settings
from app.database import get_async_session
from app.redis_client import redis_client
from app.models import Usuario
from app.exceptions import (
    NaoAutenticadoException,
    TokenExpiradoException,
    TokenInvalidoException,
    TokenRevogadoException,
    NivelInsuficienteException,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# CONFIGURAÇÕES E CONTEXTOS
# ==============================================================================

_bearer_scheme = HTTPBearer(auto_error=False)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

NIVEIS_HIERARQUIA: list[str] = ["atendente", "supervisor", "gerente", "administrador"]


# ==============================================================================
# 1. HASH DE SENHAS (NÃO-BLOQUEANTE)
# ==============================================================================

async def hash_senha(senha: str) -> str:
    """
    Gera hash bcrypt sem bloquear o event loop do FastAPI.
    
    Usa anyio.to_thread para executar bcrypt (CPU-intensivo) em thread pool,
    mantendo a aplicação responsiva.
    
    :param senha: Senha em texto puro
    :return: Hash bcrypt incluindo sal e algoritmo
    """
    return await anyio.to_thread.run_sync(_pwd_context.hash, senha)


async def verificar_senha(senha: str, hash_senha: str) -> bool:
    """
    Valida senha contra hash armazenado no banco.
    
    Nunca levanta exceção: hash corrompido retorna False para não revelar
    existência do usuário (timing-safe).
    
    :param senha: Senha em texto puro
    :param hash_senha: Hash bcrypt do banco
    :return: True se senha confere, False caso contrário
    """
    if not hash_senha:
        return False
    try:
        return await anyio.to_thread.run_sync(_pwd_context.verify, senha, hash_senha)
    except Exception:
        logger.warning("security | Hash de senha corrompido ou inválido")
        return False


# ==============================================================================
# 2. JWT: EMISSÃO E DECODIFICAÇÃO
# ==============================================================================

def criar_access_token(user_id: int, empresa_id: int, nivel: str) -> str:
    """
    Gera JWT assinado com claims multi-tenant e JTI único.
    
    :param user_id: ID do usuário (sub)
    :param empresa_id: ID do tenant para isolamento de dados
    :param nivel: Nível de acesso (RBAC)
    :return: Token JWT assinado
    """
    agora = datetime.now(timezone.utc)
    expiracao = agora + settings.jwt_expire_timedelta
    
    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,  # ID único para blacklist
        "empresa_id": empresa_id, # Multi-tenant
        "nivel": nivel,           # RBAC
        "iat": agora,
        "exp": expiracao,
        "iss": "EcoChatBot-MA",
        "aud": "ecochatbot-frontend",
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict[str, Any]:
    """
    Valida assinatura, expiração, issuer e audience do JWT.
    
    :param token: Token JWT a ser validado
    :return: Payload decodificado
    :raises TokenExpiradoException: Se token expirou
    :raises TokenInvalidoException: Se assinatura/claims inválidos
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="ecochatbot-frontend",
            issuer="EcoChatBot-MA",
        )
    except JWTError as e:
        logger.warning(f"security | Falha na decodificação JWT: {str(e)}")
        if "expired" in str(e).lower():
            raise TokenExpiradoException()
        raise TokenInvalidoException(str(e))


# ==============================================================================
# 3. BLACKLIST DE TOKENS (REDIS)
# ==============================================================================

async def revogar_token(jti: str, exp_timestamp: int) -> None:
    """
    Adiciona token à blacklist no Redis com TTL automático.
    
    O TTL é calculado para que a chave expire junto com o token, evitando
    inchaço desnecessário do Redis.
    
    :param jti: JWT ID único do token
    :param exp_timestamp: Timestamp de expiração do token
    """
    ttl = exp_timestamp - int(datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await redis_client.setex(f"revoked_token:{jti}", ttl, "1")
        logger.debug(f"security | Token revogado adicionado à blacklist | jti={jti}")


async def token_esta_revogado(jti: str) -> bool:
    """
    Verifica em O(1) se token foi revogado (logout).
    
    :param jti: JWT ID único do token
    :return: True se revogado, False caso contrário
    """
    return bool(await redis_client.exists(f"revoked_token:{jti}"))


# ==============================================================================
# 4. FASTAPI DEPENDENCIES (GUARDIÕES)
# ==============================================================================

async def obter_usuario_atual(
    credenciais: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Usuario:
    """
    Dependency principal de autenticação.
    
    Fluxo:
    1. Extrai token do header Authorization
    2. Valida assinatura e expiração
    3. Verifica se token foi revogado (Redis)
    4. Busca usuário no banco (com eager loading de nível)
    5. Valida se usuário está ativo
    
    :return: Instância de Usuario autenticado
    :raises NaoAutenticadoException: Se token ausente ou usuário inválido
    :raises TokenRevogadoException: Se token foi revogado (logout)
    """
    if not credenciais:
        raise NaoAutenticadoException()

    # 1. Validação criptográfica
    payload = decodificar_token(credenciais.credentials)
    jti = payload.get("jti")
    usuario_id = payload.get("sub")

    if not jti or not usuario_id:
        raise TokenInvalidoException("Payload do token malformado.")

    # 2. Verificação de revogação
    if await token_esta_revogado(jti):
        logger.info(f"security | Token revogado tentou acesso | jti={jti}")
        raise TokenRevogadoException()

    # 3. Busca do usuário (assíncrono com eager loading)
    query = (
        select(Usuario)
        .options(selectinload(Usuario.nivel))
        .where(Usuario.id == int(usuario_id))
    )
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()

    if not usuario or not usuario.ativo:
        logger.warning(f"security | Acesso negado | user_id={usuario_id}")
        raise NaoAutenticadoException()

    return usuario


# ==============================================================================
# 5. RBAC (CONTROLE DE ACESSO BASEADO EM PAPÉIS)
# ==============================================================================

def ordem_nivel(nivel: Optional[str]) -> int:
    """Retorna índice hierárquico do nível (-1 se desconhecido)."""
    if not nivel:
        return -1
    try:
        return NIVEIS_HIERARQUIA.index(nivel.strip().lower())
    except ValueError:
        return -1


def tem_nivel_minimo(nivel_usuario: Optional[str], nivel_minimo: str) -> bool:
    """Verifica se nível do usuário atende ao mínimo exigido."""
    return ordem_nivel(nivel_usuario) >= ordem_nivel(nivel_minimo)


def exigir_nivel(*niveis_permitidos: str):
    """
    Dependency para validação exata de níveis.
    
    Uso:
        @router.get("/", dependencies=[Depends(exigir_nivel("gerente", "administrador"))])
    
    :param niveis_permitidos: Lista de níveis aceitos
    :return: Dependency function
    """
    async def _verificador(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        nivel_usuario = usuario.nivel.nome.lower() if usuario.nivel else None
        niveis_lower = [n.lower() for n in niveis_permitidos]
        
        if nivel_usuario not in niveis_lower:
            raise NivelInsuficienteException()
        return usuario
    return _verificador


def exigir_nivel_minimo(nivel_minimo: str):
    """
    Dependency para validação hierárquica (ex: 'gerente' aceita 'administrador').
    
    Uso:
        @router.get("/", dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
    
    :param nivel_minimo: Nível mínimo requerido
    :return: Dependency function
    :raises ValueError: Se nível_minimo não existe na hierarquia
    """
    if nivel_minimo.lower() not in NIVEIS_HIERARQUIA:
        raise ValueError(f"Nível de acesso desconhecido: {nivel_minimo}")

    async def _verificador(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        nivel_usuario = usuario.nivel.nome if usuario.nivel else None
        
        if not tem_nivel_minimo(nivel_usuario, nivel_minimo):
            raise NivelInsuficienteException()
        return usuario
    return _verificador


# ==============================================================================
# ALIAS DE COMPATIBILIDADE (para imports legados)
# ==============================================================================

get_current_user = obter_usuario_atual

__all__ = [
    # Hash
    "hash_senha",
    "verificar_senha",
    # JWT
    "criar_access_token",
    "decodificar_token",
    # Blacklist
    "revogar_token",
    "token_esta_revogado",
    # Dependencies
    "obter_usuario_atual",
    "get_current_user",
    # RBAC
    "exigir_nivel",
    "exigir_nivel_minimo",
    "tem_nivel_minimo",
    "ordem_nivel",
    # Constantes
    "NIVEIS_HIERARQUIA",
]