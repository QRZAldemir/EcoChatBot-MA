"""
Router Tenant - Usuários
Endpoints multi-tenant para gestão de usuários, isolados por cliente (tenant).
"""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_cliente, get_current_usuario
from app.exceptions import (
    UsuarioAlreadyExists,
    UsuarioInvalidPassword,
    UsuarioNotFound,
)
from app.models import Cliente, Usuario
from app.schemas.usuario import (
    ConviteResponse,
    UsuarioConvidar,
    UsuarioCreate,
    UsuarioCreateAdmin,
    UsuarioListResponse,
    UsuarioResetSenha,
    UsuarioResponse,
    UsuarioUpdate,
    UsuarioUpdateSenha,
    UsuarioUpdateStatus,
)
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/tenant/usuarios", tags=["Tenant - Usuários"])

# Níveis (nome da tabela nivel_usuario)
NIVEL_ADMIN = "administrador"
NIVEL_SUPERVISOR = "supervisor"


def _nivel_usuario(usuario: Usuario) -> Optional[str]:
    """Retorna o nome do nível do usuário (via relacionamento)."""
    return usuario.nivel.nome if usuario.nivel else None


def verificar_admin(usuario_atual: Usuario = Depends(get_current_usuario)) -> Usuario:
    """Exige nível administrador."""
    if _nivel_usuario(usuario_atual) != NIVEL_ADMIN:
        raise HTTPException(403, "Permissão negada: apenas administradores")
    return usuario_atual


def verificar_supervisor(usuario_atual: Usuario = Depends(get_current_usuario)) -> Usuario:
    """Exige nível supervisor ou administrador."""
    if _nivel_usuario(usuario_atual) not in (NIVEL_ADMIN, NIVEL_SUPERVISOR):
        raise HTTPException(403, "Permissão negada: supervisor ou admin necessário")
    return usuario_atual


@router.get("/", response_model=UsuarioListResponse)
async def list_usuarios(
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(50, ge=1, le=100, description="Itens por página"),
    nivel: Optional[str] = Query(None, description="Filtrar por nível"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_supervisor),
):
    """Lista todos os usuários do tenant (supervisor/admin)."""
    service = UsuarioService(db, cliente.id)
    filtros = {}
    if nivel:
        filtros['nivel'] = nivel
    if status:
        filtros['status'] = status
    if search:
        filtros['search'] = search
    return await service.list_all(page, limit, filtros)


@router.get("/me", response_model=UsuarioResponse)
async def get_me(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_usuario),
):
    """Obtém dados do usuário autenticado."""
    return usuario_atual


@router.get("/estatisticas")
async def get_estatisticas(
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Obtém estatísticas de usuários (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    return await service.get_estatisticas()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_supervisor),
):
    """Obtém dados de um usuário específico (supervisor/admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.get_by_id(usuario_id)
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))


@router.post("/", response_model=UsuarioResponse, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Cria um novo usuário (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.create(data)
    except UsuarioAlreadyExists as e:
        raise HTTPException(400, str(e))


@router.post("/admin", response_model=UsuarioResponse, status_code=201)
async def create_usuario_admin(
    data: UsuarioCreateAdmin,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Cria um novo usuário já ativo (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.create_admin(data)
    except UsuarioAlreadyExists as e:
        raise HTTPException(400, str(e))


@router.post("/convidar", response_model=ConviteResponse)
async def convidar_usuario(
    data: UsuarioConvidar,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Cria um convite para um novo usuário (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.convidar(data)
    except UsuarioAlreadyExists as e:
        raise HTTPException(400, str(e))


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_supervisor),
):
    """Atualiza dados de um usuário (supervisor/admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.update(usuario_id, data)
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))


@router.put("/{usuario_id}/status", response_model=UsuarioResponse)
async def update_usuario_status(
    usuario_id: int,
    data: UsuarioUpdateStatus,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Atualiza status de um usuário (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        return await service.update_status(usuario_id, data)
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))


@router.delete("/{usuario_id}", status_code=204)
async def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Remove um usuário (soft delete - apenas admin)."""
    if usuario_id == usuario_atual.id:
        raise HTTPException(400, "Não é possível remover seu próprio usuário")
    service = UsuarioService(db, cliente.id)
    try:
        await service.delete(usuario_id)
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))


@router.post("/me/senha")
async def change_password(
    data: UsuarioUpdateSenha,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_usuario),
):
    """Altera a senha do usuário autenticado."""
    service = UsuarioService(db, usuario_atual.cliente_id)
    try:
        await service.change_password(usuario_atual.id, data)
        return {"message": "Senha alterada com sucesso"}
    except UsuarioInvalidPassword as e:
        raise HTTPException(400, str(e))


@router.post("/{usuario_id}/reset-senha")
async def reset_password(
    usuario_id: int,
    data: UsuarioResetSenha,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_current_cliente),
    usuario_atual: Usuario = Depends(verificar_admin),
):
    """Reseta a senha de um usuário (apenas admin)."""
    service = UsuarioService(db, cliente.id)
    try:
        await service.reset_password(usuario_id, data)
        return {"message": "Senha resetada com sucesso"}
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))


@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Envia email de recuperação de senha (público, sem tenant)."""
    from app.services.tenant_service import TenantService

    tenant_service = TenantService(db)
    cliente = await tenant_service.get_by_usuario_email(db, email)
    if not cliente:
        raise HTTPException(404, "Email não encontrado")

    service = UsuarioService(db, cliente.id)
    try:
        return await service.forgot_password(email)
    except UsuarioNotFound as e:
        raise HTTPException(404, str(e))
