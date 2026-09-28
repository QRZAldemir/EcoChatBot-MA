"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · FastAPI Dependencies
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

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy import select
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
from app.models import Cliente, Empresa, Usuario

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

# ═══════════════════════════════════════════════════════════════════════════
# 5. DEPENDÊNCIAS DE TENANT
# ═══════════════════════════════════════════════════════════════════════════
# Estas funções vinham de `app/dependencies.py`, que foi removido: ele
# declarava `db: Session` e chamava `db.query()` numa aplicação que é
# async-only. `AsyncSession` não tem `.query()`, então qualquer rota que
# usasse aquilo quebrava em tempo de execução com AttributeError — sem
# erro na importação, o que é o tipo de falha que só aparece em produção.
#
# O QUE É TENANT AQUI
# ------------------
# A EMPRESA é o tenant. O Cliente é a conta comercial (plano, limites) e
# é uma camada ACIMA do tenant, não o tenant. Um usuário sem empresa
# ativa não tem o que ver, nem o próprio cadastro dele.


async def get_current_empresa(
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> Empresa:
    """
    Empresa do usuário autenticado — ESTE é o filtro de multi-tenant.

    Todo SELECT de dado de cliente tem que passar por aqui. Filtrar por
    `cliente_id` em vez de `empresa_id` mistura a conta comercial com o
    tenant e vaza dado entre empresas do mesmo cliente.
    """
    if usuario.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não vinculado a uma empresa ativa.",
        )

    resultado = await db.execute(
        select(Empresa).where(
            Empresa.id == usuario.empresa_id,
            Empresa.deleted_at.is_(None),
        )
    )
    empresa = resultado.scalar_one_or_none()

    if empresa is None:
        raise HTTPException(
            status_code=403,
            detail="Empresa do usuário não encontrada ou removida.",
        )
    return empresa


async def get_current_cliente(
    db: Annotated[AsyncSession, Depends(get_db)],
    empresa: Annotated[Empresa, Depends(get_current_empresa)],
) -> Cliente:
    """
    Conta COMERCIAL do usuário (plano, limite de canais, limite de usuários).

    Usado só onde a pergunta é "quanto esta empresa pode usar", não "de quem
    é este dado". Para dado, use `get_current_empresa`.
    """
    if empresa.cliente_id is None:
        raise HTTPException(
            status_code=403,
            detail="Empresa sem vínculo com uma conta comercial.",
        )

    resultado = await db.execute(
        select(Cliente).where(
            Cliente.id == empresa.cliente_id,
            Cliente.deleted_at.is_(None),
        )
    )
    cliente = resultado.scalar_one_or_none()

    if cliente is None:
        raise HTTPException(
            status_code=403,
            detail="Conta comercial não encontrada ou removida.",
        )
    return cliente


# ── Atalhos para deixar a assinatura das rotas limpa ──────────────────────────
CurrentEmpresa = Annotated[Empresa, Depends(get_current_empresa)]
CurrentCliente = Annotated[Cliente, Depends(get_current_cliente)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]


__all__ = [
    # banco
    "get_db", "get_mongo", "get_redis_client",
    # autenticação
    "get_token_payload", "get_current_user",
    # RBAC
    "require_nivel", "require_nivel_minimo",
    "require_admin", "require_gerente", "require_supervisor",
    "require_atendente_ou_superior",
    # tenant
    "get_current_empresa", "get_current_cliente",
    # aliases
    "DBSession", "MongoDB", "RedisClient", "TokenPayload",
    "CurrentEmpresa", "CurrentCliente", "CurrentUser",
]

"""
Adicionar ao final de backend/app/deps.py
"""

from app.models.empresa_models import Empresa


# ═══════════════════════════════════════════════════════════════════════════
# EMPRESA ATUAL — resolve e injeta o tenant
# ═══════════════════════════════════════════════════════════════════════════

async def get_current_empresa(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Empresa:
    """
    Empresa do usuário autenticado — ESTE é o filtro de multi-tenant.

    ─────────────────────────────────────────────────────────────────────
    POR QUE ESTA DEPENDÊNCIA EXISTE
    ─────────────────────────────────────────────────────────────────────
    Antes, cada endpoint lia `user.empresa_id` manualmente — fácil de
    esquecer e difícil de auditar. Agora, o endpoint declara:

        empresa: CurrentEmpresa = Depends()

    E o FastAPI injeta automaticamente. Se o usuário não tiver empresa
    ativa, a própria dependência barra com 403 ANTES de chegar no service.

    ─────────────────────────────────────────────────────────────────────
    REGRA
    ─────────────────────────────────────────────────────────────────────
    Este é o ÚNICO lugar autorizado a resolver a empresa do usuário.
    Nenhum endpoint deve ler `user.empresa_id` diretamente.
    """
    if user.empresa_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não vinculado a uma empresa ativa.",
        )

    stmt = select(Empresa).where(
        Empresa.id == user.empresa_id,
        Empresa.deleted_at.is_(None),
    )
    empresa = (await db.execute(stmt)).scalar_one_or_none()
    if empresa is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa do usuário não encontrada ou removida.",
        )
    return empresa


# Aliases
CurrentEmpresa = Annotated[Empresa, Depends(get_current_empresa)]
