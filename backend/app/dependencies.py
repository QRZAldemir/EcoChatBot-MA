"""
Dependências de tenant para routers multi-tenant.

get_current_usuario: retorna o usuário autenticado (via security).
get_current_cliente: resolve o Cliente/tenant do usuário autenticado.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import obter_usuario_atual
from app.models import Cliente, Usuario
from app.services.tenant_service import TenantService


def get_current_usuario(
    usuario: Usuario = Depends(obter_usuario_atual),
) -> Usuario:
    """Retorna o usuário autenticado (com dados completos)."""
    return usuario


def get_current_cliente(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Cliente:
    """Resolve o Cliente/tenant do usuário autenticado."""
    service = TenantService(db)
    cliente = service.get_by_usuario(db, usuario)
    if not cliente:
        raise HTTPException(
            status_code=403,
            detail="Usuário não vinculado a um cliente/tenant ativo.",
        )
    return cliente
