"""
Dependências de tenant para routers multi-tenant.

get_current_usuario: retorna o usuário autenticado (via security).
get_current_cliente: resolve o Cliente/tenant do usuário autenticado.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import obter_usuario_atual
from app.models.mixins import SoftDeleteMixin
from app.models import Cliente, Empresa, Usuario
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


def get_current_empresa(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Empresa:
    """
    Resolve a EMPRESA do usuário autenticado — que é o TENANT.

    Este é o que os routers multi-tenant devem usar para filtrar dado. Um
    usuário sem empresa ativa não tem o que ver: nem o próprio cadastro dele.

    `get_current_cliente` continua existindo, mas resolve a conta COMERCIAL
    (plano, limites), que é outra coisa — não é o tenant.
    """
    if usuario.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não vinculado a uma empresa ativa.",
        )
    empresa = (
        db.query(Empresa)
        .filter(
            Empresa.id == usuario.empresa_id,
            Empresa.deleted_at.is_(None),
        )
        .first()
    )
    if not empresa:
        raise HTTPException(
            status_code=403,
            detail="Empresa do usuário não encontrada ou removida.",
        )
    return empresa
