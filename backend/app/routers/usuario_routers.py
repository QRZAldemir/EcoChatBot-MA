# =============================================================================

"""
Router de Usuários — camada HTTP (FastAPI).

Este módulo faz a ponte entre o cliente (frontend/mobile) e a camada de
serviço (`UsuarioService`). Aqui só mora:

    - Declaração de rotas e verbos HTTP.
    - Dependências (DB, autenticação, nível de acesso).
    - Conversão de erros de negócio em HTTPException.
    - Documentação OpenAPI (summary, description, responses).

Toda a regra de negócio (hash de senha, validação de empresa + Meta,
vínculo de conexões, unicidade de email por empresa, isolamento
multi-tenant) vive em `UsuarioService`.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import exigir_nivel, exigir_nivel_minimo, get_current_user
from app.services.usuario_service import UsuarioService
from app.schemas.usuario_schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioListItem,
)


# =============================================================================
# CONFIGURAÇÃO DO ROUTER
# Prefixo, tags e respostas de erro comuns centralizados.
# =============================================================================

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Sem permissão para o nível exigido"},
        404: {"description": "Usuário não encontrado"},
        409: {"description": "Conflito (ex.: e-mail já cadastrado)"},
        422: {"description": "Empresa sem id_telefone_meta configurado na Meta"},
    },
)


# =============================================================================
# ENDPOINTS — LEITURA
# =============================================================================

@router.get(
    "/",
    response_model=UsuarioListResponse,
    summary="Lista usuários (paginado)",
    description=(
        "Retorna usuários da empresa do solicitante com paginação e filtros. "
        "O `empresa_id` é sempre extraído do token — nunca do query string — "
        "para garantir isolamento multi-tenant. "
        "Requer nível mínimo: **supervisor**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("supervisor"))],
)
def listar_usuarios(
    nome: Optional[str] = Query(
        None, max_length=100, description="Filtro por nome (case-insensitive)"
    ),
    departamento_id: Optional[int] = Query(
        None, description="Filtro por departamento"
    ),
    canal_id: Optional[int] = Query(
        None, description="Filtro por canal"
    ),
    nivel: Optional[str] = Query(
        None, max_length=20,
        description="Nome do nível (atendente|supervisor|gerente|administrador)"
    ),
    status_: Optional[str] = Query(
        None, alias="status", max_length=20,
        description="Status do usuário (ativo|inativo|suspenso)"
    ),
    page: int = Query(1, ge=1, description="Página (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página (máx 100)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Lista usuários paginados da empresa do usuário autenticado.

    Filtros opcionais: nome, departamento, canal, nível e status.
    Retorna um envelope com `total`, `page`, `limit` e `data`.
    """
    total, usuarios = UsuarioService.listar_usuarios(
        db=db,
        empresa_id=current_user.empresa_id,   # 🔒 sempre do token
        nome=nome,
        departamento_id=departamento_id,
        canal_id=canal_id,
        nivel=nivel,
        status=status_,
        page=page,
        limit=limit,
    )

    data: List[UsuarioListItem] = [
        UsuarioListItem(
            id=u.id,
            nome=u.nome,
            email=u.email,
            telefone=u.telefone,
            ativo=u.ativo,
            empresa_id=u.empresa_id,
            nivel_nome=u.nivel.nome if u.nivel else None,
            departamento_nome=u.departamento.nome if u.departamento else None,
            canal_nome=u.canal.nome if u.canal else None,
        )
        for u in usuarios
    ]

    return UsuarioListResponse(total=total, page=page, limit=limit, data=data)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Busca usuário por ID",
    description=(
        "Retorna dados completos de um usuário, incluindo a empresa vinculada "
        "e o `id_telefone_meta` (número registrado na Meta/WhatsApp Business). "
        "Requer nível mínimo: **supervisor**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("supervisor"))],
)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Busca um usuário pelo ID dentro da mesma empresa do solicitante."""
    usuario = UsuarioService.buscar_por_id(
        db=db,
        usuario_id=usuario_id,
        empresa_id=current_user.empresa_id,
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return usuario


# =============================================================================
# ENDPOINTS — ESCRITA
# =============================================================================

@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria usuário",
    description=(
        "Cria um usuário vinculado a uma empresa. A empresa **DEVE** possuir "
        "`id_telefone_meta` ativo (número registrado na Meta/WhatsApp Business "
        "API), caso contrário retorna 422. "
        "Gestor/supervisor só pode criar na própria empresa; admin global "
        "pode escolher a empresa no body. "
        "Requer nível mínimo: **gerente**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("gerente"))],
)
def criar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Cria um usuário.

    Regras aplicadas no `UsuarioService`:
        1. Empresa existe e está ativa.
        2. Empresa possui `id_telefone_meta` válido na Meta.
        3. Gestor/supervisor só cria na própria empresa.
        4. Email único dentro da empresa (multi-tenant).
        5. Senha recebe hash (bcrypt/argon2).
        6. Conexões são validadas contra a empresa.
    """
    # 🔒 Gestor/supervisor só cria na própria empresa
    if (
        not getattr(current_user, "is_admin_global", False)
        and usuario.empresa_id != current_user.empresa_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode criar usuários na sua própria empresa",
        )

    return UsuarioService.criar_usuario(
        db=db,
        dados=usuario,
        empresa_id=usuario.empresa_id,
    )


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualiza usuário",
    description=(
        "Atualiza parcialmente um usuário (apenas campos enviados). "
        "O vínculo com a empresa (`empresa_id`) é **imutável** e não existe "
        "no payload de atualização. "
        "Requer nível mínimo: **gerente**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("gerente"))],
)
def atualizar_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Atualiza um usuário.

    - `empresa_id` NÃO pode ser alterado (imutável por design).
    - Email, se alterado, é revalidado como único na empresa.
    - `conexoes_ids`, se enviado, reconcilia os vínculos (remove antigos,
      adiciona novos validados contra a empresa).
    """
    atualizado = UsuarioService.atualizar_usuario(
        db=db,
        usuario_id=usuario_id,
        dados=usuario,
        empresa_id=current_user.empresa_id,
    )
    if not atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return atualizado


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove usuário (soft delete)",
    description=(
        "Realiza **soft delete** do usuário (marca `ativo=False` e "
        "`status='inativo'`), preservando histórico e auditoria. "
        "Requer nível: **administrador**."
    ),
    dependencies=[Depends(exigir_nivel("administrador"))],
)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Remove (soft delete) um usuário da empresa do solicitante.

    Retorna 204 em caso de sucesso, 404 se não existir na empresa.
    """
    sucesso = UsuarioService.deletar_usuario(
        db=db,
        usuario_id=usuario_id,
        empresa_id=current_user.empresa_id,
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return None


# =============================================================================
# FIM DO ARQUIVO — app/routers/usuarios_routers.py
