"""
Router Tenant - Atendimentos
Endpoints multi-tenant para gestão de atendimentos, isolados por usuário/tenant.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import obter_usuario_atual
from app.models import Usuario, Atendimento
from app.schemas.atendimento import (
    FiltroAtendimento,
    AtendimentoCreate,
    AtendimentoUpdate,
    AtendimentoTransferir,
    AtendimentoFinalizar,
    AtendimentoResponse,
    AtendimentoDetalhado,
    AtendimentoIndicadores
)
from app.services.atendimento_service import AtendimentoService

router = APIRouter(prefix="/tenant/atendimentos", tags=["Tenant - Atendimentos"])


@router.get("/", response_model=dict)
async def listar_atendimentos(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    status: Optional[str] = None,
    departamento_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    cliente_whatsapp: Optional[str] = None,
    protocolo: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Lista atendimentos do tenant com filtros.
    Usa o usuario_atual como contexto de tenant (cliente_id).
    """
    service = AtendimentoService(db)

    filtros = FiltroAtendimento(
        status=status,
        departamento_id=departamento_id,
        usuario_id=usuario_id,
        cliente_whatsapp=cliente_whatsapp,
        protocolo=protocolo,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

    result = await service.listar(filtros, page, limit, order)
    return result


@router.get("/indicadores", response_model=AtendimentoIndicadores)
async def indicadores(
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Obtém indicadores de atendimento em tempo real.
    NOTA: Este endpoint deve vir ANTES de /{atendimento_id} para evitar conflito de rota.
    """
    service = AtendimentoService(db)

    try:
        indicadores = await service.indicadores(data_inicio, data_fim)
        return indicadores
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/{atendimento_id}", response_model=AtendimentoDetalhado)
async def buscar_atendimento(
    atendimento_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Busca um atendimento específico.
    """
    service = AtendimentoService(db)

    try:
        atendimento = await service.buscar_por_id(atendimento_id, usuario_atual.id)
        return atendimento
    except Exception as e:
        raise HTTPException(404, str(e))


@router.post("/", response_model=AtendimentoResponse, status_code=201)
async def criar_atendimento(
    data: AtendimentoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Cria um novo atendimento.
    """
    service = AtendimentoService(db)

    try:
        atendimento = await service.criar(data)
        return atendimento
    except Exception as e:
        raise HTTPException(400, str(e))


@router.put("/{atendimento_id}", response_model=AtendimentoResponse)
async def atualizar_atendimento(
    atendimento_id: int,
    data: AtendimentoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Atualiza um atendimento existente.
    """
    service = AtendimentoService(db)

    try:
        atendimento = await service.atualizar(atendimento_id, data, usuario_atual.id)
        return atendimento
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{atendimento_id}/transferir", response_model=AtendimentoResponse)
async def transferir_atendimento(
    atendimento_id: int,
    data: AtendimentoTransferir,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Transfere atendimento para outro departamento/atendente.
    """
    service = AtendimentoService(db)

    try:
        atendimento = await service.transferir(atendimento_id, data, usuario_atual.id)
        return atendimento
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{atendimento_id}/finalizar", response_model=AtendimentoResponse)
async def finalizar_atendimento(
    atendimento_id: int,
    data: Optional[AtendimentoFinalizar] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Finaliza um atendimento.
    """
    service = AtendimentoService(db)

    try:
        atendimento = await service.finalizar(atendimento_id, data, usuario_atual.id)
        return atendimento
    except Exception as e:
        raise HTTPException(400, str(e))
