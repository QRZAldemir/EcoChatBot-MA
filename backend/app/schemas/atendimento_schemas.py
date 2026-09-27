# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.routers.atendimentos_routers
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-27
# VERSÃO: 4.1.0 (Alinhamento total com atendimento_schemas.py v2.1.0)
# ==============================================================================
"""
FUNCIONALIDADE
--------------
Endpoints HTTP para o domínio de Atendimento. 
Consome os schemas Pydantic ricos em domínio (ex: AtendimentoTransferir com 
suporte a ramal_destino e menu_item_id), garantindo que a lógica de URA/Telefonia 
e mensageria seja preservada.

SEGURANÇA E MULTI-TENANCY
-------------------------
Todos os endpoints injetam `CurrentEmpresa`. O `empresa_id` é aplicado 
implicitamente na camada de Service, prevenindo IDOR (Insecure Direct Object Reference).
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Dependências e Schemas do Projeto
from app.database import get_db
from app.deps import CurrentEmpresa
from app.schemas.atendimento_schemas import (
    FiltroAtendimento,
    AtendimentoCreate,
    AtendimentoUpdate,
    AtendimentoTransferir,
    AtendimentoFinalizar,
    AtendimentoResponse,
    AtendimentoDetalhado,
    AtendimentoIndicadores,
)
from app.services.atendimento_service import AtendimentoService
from app.exceptions import RecursoNaoEncontradoError, ValidacaoNegocioError

router = APIRouter(prefix="/atendimentos", tags=["Atendimentos"])


# ==============================================================================
# SEÇÃO 1: CONSULTAS (GET)
# ==============================================================================

@router.get(
    "/", 
    response_model=dict[str, Any], 
    summary="Listar atendimentos com filtros avançados"
)
async def listar_atendimentos(
    filtros: FiltroAtendimento = Depends(),
    db: AsyncSession = Depends(get_db),
    empresa: CurrentEmpresa = Depends(),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """
    Lista atendimentos da empresa autenticada, aplicando os filtros de domínio
    (tipo_canal, status, datas, etc.) definidos em FiltroAtendimento.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    
    resultado = await service.listar(
        filtros=filtros,
        page=page,
        limit=limit,
    )
    
    return {
        "total": resultado["total"],
        "page": resultado["page"],
        "limit": resultado["limit"],
        "total_pages": (resultado["total"] + limit - 1) // limit,
        "registros": [AtendimentoResponse.model_validate(r) for r in resultado["registros"]]
    }


@router.get(
    "/indicadores", 
    response_model=AtendimentoIndicadores,
    summary="Obter indicadores e métricas de atendimento"
)
async def obter_indicadores(
    filtros: FiltroAtendimento = Depends(),
    db: AsyncSession = Depends(get_db),
    empresa: CurrentEmpresa = Depends(),
) -> AtendimentoIndicadores:
    """Retorna métricas consolidadas (tempos médios, totais por status/departamento)."""
    service = AtendimentoService(db, empresa_id=empresa.id)
    dados = await service.obter_indicadores(filtros=filtros)
    return AtendimentoIndicadores.model_validate(dados)


@router.get(
    "/{atendimento_id}", 
    response_model=AtendimentoDetalhado,
    summary="Buscar atendimento detalhado por ID"
)
async def buscar_atendimento(
    atendimento_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: CurrentEmpresa = Depends(),
) -> AtendimentoDetalhado:
    """
    Recupera um atendimento com dados calculados (tempo de espera, tempo de atendimento).
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    atendimento = await service.buscar_detalhado(atendimento_id)
    
    if not atendimento:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado ou acesso negado.")
        
    return AtendimentoDetalhado.model_validate(atendimento)


# ==============================================================================
# SEÇÃO 2: ESCRITA E AÇÕES DE DOMÍNIO (POST, PATCH)
# ==============================================================================

@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED, 
    response_model=AtendimentoResponse,
    summary="Criar novo atendimento"
)
async def criar_atendimento(
    payload: AtendimentoCreate,
    db: AsyncSession = Depends(get_db),
    empresa: CurrentEmpresa = Depends(),
) -> AtendimentoResponse:
    """
    Inicia um novo atendimento. O schema AtendimentoCreate já valida o telefone 
    e exige o tipo_canal (ex: pabx, whatsapp).
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    novo_atendimento = await service.criar(**payload.model_dump())
    return AtendimentoResponse.model_validate(novo_atendimento)


@router.patch(
    "/{atendimento_id}", 
    response_model=AtendimentoResponse,
    summary="Atualizar dados cadastrais do atendimento"
)
async