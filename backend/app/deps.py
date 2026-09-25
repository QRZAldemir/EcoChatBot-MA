"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · FastAPI Dependencies
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     deps.py
@module   Backend / App / Deps
@author   Aldemir Queiroz
@since    2026
@version  1.1.0 (Refatorado para eliminar imports circulares e redundâncias)
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Centraliza as DEPENDÊNCIAS (injeção) usadas nos routers FastAPI, atuando
como uma fachada limpa e tipada sobre as camadas de banco de dados e segurança.

    1. `get_db`             → Sessão assíncrona SQLAlchemy (PostgreSQL)
    2. `get_mongo`          → Instância do banco MongoDB (Motor)
    3. `get_redis_client`   → Instância do cliente Redis assíncrono
    4. `get_token_payload`  → Extrai e valida o JWT (sem buscar no DB)
    5. `get_current_user`   → Retorna o objeto `Usuario` validado (com DB)
    6. `require_nivel`      → Factory de guards RBAC (nível exato)
    7. `require_nivel_minimo` → Factory de guards RBAC (hierárquico)
    8. Atalhos RBAC         → `require_admin`, `require_gerente`, etc.

RELACIONAMENTO COM OUTROS OBJETOS DO PROJETO
────────────────────────────────────────────
    deps.py (este arquivo)
        │
        ├──► app/database.py       • Re-exporta a sessão assíncrona
        ├──► app/mongodb.py        • Re-exporta a instância do DB
        ├──► app/redis_client.py   • Re-exporta o cliente Redis
        ├──► app/security.py       • Delega toda a lógica de JWT, Blacklist e RBAC
        └──► app/routers/*.py      • Fornece as dependências tipadas via `Annotated`

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Agnóstico de canal e segmento. O `empresa_id` é validado no payload do JWT.

USO
───
    from fastapi import APIRouter
    from app.deps import DBSession, CurrentUser, require_admin

    router = APIRouter()

    @router.get('/usuarios')
    async def listar_usuarios(
        db: DBSession,
        user: CurrentUser,
    ):
        # user é um objeto Usuario tipado, já validado e com 'nivel' carregado
        ...

    @router.delete('/usuarios/{id}')
    async def deletar_usuario(
        id: int,
        db: DBSession,
        _: None = Depends(require_admin), # Bloqueia se não for admin
    ):
        ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Importações das camadas inferiores (Banco de Dados)
from app.database import get_async_session as _get_db
from app.mongodb import get_mongo_db as _get_mongo
from app.redis_client import get_redis as _get_redis

# 2. Importações da camada de Segurança (Lógica pesada delegada aqui)
from app.security import (
    decodificar_token,
    obter_usuario_atual,
    exigir_nivel,
    exigir_nivel_minimo,
)
from app.models import Usuario

# Esquema padrão para extração do header "Authorization: Bearer <token>"
_bearer_scheme = HTTPBearer(auto_error=True)


# ═══════════════════════════════════════════════════════════════════════════
# 1. DEPENDÊNCIAS DE BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

async def get_db() -> AsyncSession:
    """Dependência: Yield de sessão PostgreSQL assíncrona com gerenciamento de transação."""
    async for session in _get_db():
        yield session


def get_mongo() -> AsyncIOMotorDatabase:
    """Dependência: Retorna a instância do banco MongoDB (Singleton gerenciado pelo lifespan)."""
    return _get_mongo()


def get_redis_client() -> Redis:
    """Dependência: Retorna a instância do cliente Redis (Singleton gerenciado pelo lifespan)."""
    return _get_redis()


# ═══════════════════════════════════════════════════════════════════════════
# 2. DEPENDÊNCIAS DE AUTENTICAÇÃO (JWT)
# ═══════════════════════════════════════════════════════════════════════════

async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)]
) -> dict[str, Any]:
    """
    Extrai e decodifica o JWT do header. 
    NÃO consulta o banco de dados. Ideal para rotas que só precisam validar a assinatura.
    
    Raises:
        TokenInvalidoException / TokenExpiradoException (vindos de security.py)
    """
    return decodificar_token(credentials.credentials)


# Re-exportação da dependência robusta de usuário.
# Isso evita importação circular com `usuario_service` e centraliza a query com `selectinload`.
get_current_user = obter_usuario_atual


# ═══════════════════════════════════════════════════════════════════════════
# 3. DEPENDÊNCIAS DE AUTORIZAÇÃO (RBAC)
# ═══════════════════════════════════════════════════════════════════════════

def require_nivel(*niveis: str) -> Callable:
    """
    Factory: Exige que o usuário tenha um dos níveis exatos informados.
    Uso: dependencies=[Depends(require_nivel("gerente", "administrador"))]
    """
    return exigir_nivel(*niveis)


def require_nivel_minimo(nivel: str) -> Callable:
    """
    Factory: Exige que o usuário tenha o nível informado ou superior na hierarquia.
    Hierarquia: atendente < supervisor < gerente < administrador
    Uso: dependencies=[Depends(require_nivel_minimo("gerente"))]
    """
    return exigir_nivel_minimo(nivel)


# ── Atalhos Práticos para Routers ──
require_admin = require_nivel_minimo("administrador")
require_gerente = require_nivel_minimo("gerente")
require_supervisor = require_nivel_minimo("supervisor")
require_atendente_ou_superior = require_nivel_minimo("atendente")


# ═══════════════════════════════════════════════════════════════════════════
# 4. ALIASES TIPOS (Type Aliases) para Routers Limpos
# ═══════════════════════════════════════════════════════════════════════════
# O uso de Annotated aqui permite que os routers fiquem extremamente legíveis,
# sem poluir a assinatura das funções com `Depends(...)`.

DBSession = Annotated[AsyncSession, Depends(get_db)]
MongoDB = Annotated[AsyncIOMotorDatabase, Depends(get_mongo)]
RedisClient = Annotated[Redis, Depends(get_redis_client)]
TokenPayload = Annotated[dict[str, Any], Depends(get_token_payload)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]