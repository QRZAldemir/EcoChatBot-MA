# ==============================================================================
# ARQUIVO.....: app/routers/tenant/usuario_router.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBotMarcx - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Router REST do Objeto Usuario (isolado por tenant)
# VERSÃO......: 3.0.0
# CRIADO EM...: 2024-01-15
# ATUALIZADO..: 2026-09-19
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: FastAPI + SQLAlchemy 2.0
# ==============================================================================
# DESCRIÇÃO...:
# Camada HTTP do objeto Usuario. Expõe endpoints REST sob o prefixo
# /api/tenant/usuarios. empresa_id é SEMPRE extraído do token JWT,
# nunca do body/query (anti-IDOR).
#
# FUNCIONALIDADES:
# 1. Listagem paginada com filtros
# 2. Detalhe por ID (com conexões expandidas)
# 3. Criação de usuário
# 4. Atualização parcial
# 5. Soft delete
# 6. Alteração de senha própria
# 7. Reset de senha (admin)
# 8. Convite de usuário
# 9. Estatísticas agregadas
#
# SEGURANÇA:
# - empresa_id SEMPRE do token
# - Helpers de serialização (_to_response, _to_list_item)
# - HTTPException propagadas do Service
#
# DEPENDÊNCIAS:
# - app.dependencies.get_current_cliente / get_current_usuario
# - app.services.usuario_service.UsuarioService
# - app.schemas.usuario_schemas (DTOs)
#
# USADO POR:
# - app.main (include_router)
# ==============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_cliente, get_current_usuario
from app.models import Cliente, Usuario
from app.schemas.usuario_schemas import (
    ConexaoResponse,
    UsuarioConvidar,
    UsuarioCreate,
    UsuarioListItem,
    UsuarioListResponse,
    UsuarioResetSenha,
    UsuarioResponse,
    UsuarioUpdate,
    UsuarioUpdateSenha,
)
from app.services.usuario_service import UsuarioService

router = APIRouter(
    prefix="/api/tenant/usuarios",
    tags=["Tenant - Usuários"],
    responses={
        401: {"description": "Não autenticado"},
        404: {"description": "Usuário não encontrado"},
        409: {"description": "Conflito (e-mail ou login já cadastrado)"},
        422: {"description": "Empresa sem conexões ativas configuradas"},
    },
)


# ==============================================================================
# HELPERS DE SERIALIZAÇÃO
# ==============================================================================
def _to_response(u: Usuario) -> UsuarioResponse:
    """Converte ORM Usuario em UsuarioResponse (com expansões)."""
    return UsuarioResponse(
        id=u.id,
        empresa_id=u.empresa_id,
        empresa_nome=u.empresa.nome if u.empresa else None,
        nome=u.nome,
        usuario=u.usuario,
        email=u.email,
        telefone=u.telefone,
        foto=u.foto,
        nivel_id=u.nivel_id,
        nivel_nome=u.nivel.nome if u.nivel else None,
        departamento_id=u.departamento_id,
        departamento_nome=u.departamento.nome if u.departamento else None,
        canal_id=u.canal_id,
        canal_nome=u.canal.nome if u.canal else None,
        turno_id=u.turno_id,
        turno_nome=u.turno.nome if u.turno else None,
        ativo=u.ativo,
        status=u.status,
        conexoes=[
            ConexaoResponse(
                id=c.id,
                nome_identificador=c.nome_identificador,
                id_telefone=c.id_telefone,
                numero_telefone=c.numero_telefone,
                canal_nome=c.canal.nome if c.canal else None,
            )
            for c in (u.conexoes or [])
        ],
        conexao_padrao_id=u.conexao_padrao_id,
        criado_em=u.criado_em,
        atualizado_em=u.atualizado_em,
    )


def _to_list_item(u: Usuario) -> UsuarioListItem:
    """Converte ORM Usuario em UsuarioListItem (resumido)."""
    return UsuarioListItem(
        id=u.id,
        nome=u.nome,
        usuario=u.usuario,
        email=u.email,
        telefone=u.telefone,
        foto=u.foto,
        ativo=u.ativo,
        status=u.status,
        nivel_nome=u.nivel.nome if u.nivel else None,
        departamento_nome=u.departamento.nome if u.departamento else None,
        canal_nome=u.canal.nome if u.canal else None,
        turno_nome=u.turno.nome if u.turno else None,
        qtd_conexoes=len(u.conexoes) if u.conexoes else 0,
    )


# ==============================================================================
# ENDPOINTS — LEITURA
# ==============================================================================
@router.get("/", response_model=UsuarioListResponse)
def listar_usuarios(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    nome: Optional[str] = Query(None, max_length=100),
    departamento_id: Optional[int] = Query(None),
    status_: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Lista usuários paginados do tenant autenticado."""
    svc = UsuarioService(db, cliente.id)
    total, usuarios = svc.listar_usuarios(page, limit, {
        "nome": nome,
        "departamento_id": departamento_id,
        "status": status_,
    })
    return UsuarioListResponse(
        total=total, page=page, limit=limit,
        data=[_to_list_item(u) for u in usuarios],
    )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Busca usuário por ID."""
    svc = UsuarioService(db, cliente.id)
    usuario = svc.buscar_por_id(usuario_id)

    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")

    return _to_response(usuario)


# ==============================================================================
# ENDPOINTS — ESCRITA
# ==============================================================================
@router.post("/", response_model=UsuarioResponse, status_code=201)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Cria usuário vinculado ao tenant autenticado."""
    svc = UsuarioService(db, cliente.id)
    return _to_response(svc.criar_usuario(dados))


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Atualiza parcialmente um usuário."""
    svc = UsuarioService(db, cliente.id)
    return _to_response(svc.atualizar_usuario(usuario_id, dados))


@router.delete("/{usuario_id}", status_code=204)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Soft delete de usuário."""
    svc = UsuarioService(db, cliente.id)

    if not svc.deletar_usuario(usuario_id):
        raise HTTPException(404, "Usuário não encontrado")

    return None


# ==============================================================================
# ENDPOINTS — SENHA
# ==============================================================================
@router.post("/me/senha")
def alterar_minha_senha(
    dados: UsuarioUpdateSenha,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_usuario),
):
    """Altera senha do próprio usuário autenticado."""
    svc = UsuarioService(db, usuario_atual.empresa_id)
    svc.alterar_senha(usuario_atual.id, dados)
    return {"message": "Senha alterada com sucesso"}


@router.post("/{usuario_id}/reset-senha")
def resetar_senha(
    usuario_id: int,
    dados: UsuarioResetSenha,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Reseta senha de usuário (admin)."""
    svc = UsuarioService(db, cliente.id)
    svc.resetar_senha(usuario_id, dados)
    return {"message": "Senha resetada com sucesso"}


# ==============================================================================
# ENDPOINTS — CONVITE E ESTATÍSTICAS
# ==============================================================================
@router.post("/convidar", response_model=UsuarioResponse, status_code=201)
def convidar_usuario(
    dados: UsuarioConvidar,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Cria usuário inativo com senha temporária."""
    svc = UsuarioService(db, cliente.id)
    return _to_response(svc.convidar_usuario(dados))


@router.get("/estatisticas/resumo")
def estatisticas(
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
):
    """Retorna contagem agregada de usuários do tenant."""
    svc = UsuarioService(db, cliente.id)
    return svc.get_estatisticas()