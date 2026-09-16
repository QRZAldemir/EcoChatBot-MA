"""
================================================================================
MÓDULO: app/routers/canal.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-16
VERSÃO: 2.0.0
OBJETIVO: Define os endpoints REST API para gestão de canais omnichannel.
          Implementa CRUD completo, métricas e configuração de webhooks.
PASTA: backend/app/routers/
================================================================================
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.canal import (
    CanalCreate,
    CanalUpdate,
    CanalResponse,
    CanalDetalhado,
    CanalListaResponse,
    CanalMetricasResumo
)
from app.services.canal_service import CanalService
from app.auth import get_current_user, UsuarioAuth
from app.utils.zig_response import ZigResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/canais",
    tags=["Canais - Omnichannel"],
    responses={404: {"description": "Canal não encontrado"}}
)


# ==============================================================================
# ENDPOINTS DE CRUD
# ==============================================================================

@router.post(
    "/",
    response_model=ZigResponse[CanalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo canal",
    description="Cria um novo canal de comunicação para a empresa do usuário autenticado."
)
async def criar_canal(
    canal_data: CanalCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Cria um novo canal de comunicação.
    
    - **nome**: Nome amigável do canal (obrigatório)
    - **tipo**: Tipo do canal (whatsapp, telegram, instagram, etc.)
    - **identificador**: Token/número/ID técnico (obrigatório)
    - **descricao**: Descrição opcional
    - **configuracao**: JSON com settings específicos
    - **departamento_id**: Departamento responsável (opcional)
    
    O webhook será configurado automaticamente após a criação.
    """
    try:
        service = CanalService(db)
        
        # Extrair cliente_id do usuário autenticado
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        if not cliente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não vinculado a nenhuma empresa"
            )
        
        canal = service.criar_canal(canal_data, cliente_id)
        
        return ZigResponse(
            codigo=0,
            mensagem="Canal criado com sucesso",
            dados=canal
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar canal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=ZigResponse[CanalListaResponse],
    summary="Listar canais",
    description="Lista todos os canais da empresa com paginação e filtros."
)
async def listar_canais(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(50, ge=1, le=100, description="Limite por página"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Lista canais da empresa autenticada.
    
    - **page**: Página atual (1-based)
    - **limit**: Registros por página (máx 100)
    - **tipo**: Filtrar por tipo (whatsapp, telegram, etc.)
    - **ativo**: Filtrar por status (True/False)
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        canais, total = service.listar_canais(
            cliente_id=cliente_id,
            page=page,
            limit=limit,
            tipo=tipo,
            ativo=ativo
        )
        
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return ZigResponse(
            codigo=0,
            mensagem="Canais listados com sucesso",
            dados=CanalListaResponse(
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages,
                canais=canais
            )
        )
    
    except Exception as e:
        logger.error(f"Erro ao listar canais: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{canal_id}",
    response_model=ZigResponse[CanalDetalhado],
    summary="Buscar canal por ID",
    description="Retorna dados detalhados de um canal específico."
)
async def buscar_canal(
    canal_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Busca um canal específico por ID.
    
    Retorna dados completos incluindo métricas de uso.
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        canal = service.buscar_por_id(canal_id, cliente_id)
        
        # Obter métricas
        metricas = service.obter_metricas_canal(canal_id, cliente_id)
        
        canal_detalhado = CanalDetalhado(
            **{
                "id": canal.id,
                "cliente_id": canal.cliente_id,
                "nome": canal.nome,
                "descricao": canal.descricao,
                "tipo": canal.tipo,
                "identificador": canal.identificador,
                "configuracao": canal.configuracao_json,
                "departamento_id": canal.departamento_id,
                "ativo": canal.ativo,
                "webhook_url": canal.webhook_url,
                "webhook_verify_token": canal.webhook_verify_token,
                "criado_em": canal.criado_em,
                "atualizado_em": canal.atualizado_em,
                "ultimo_sync": canal.ultimo_sync,
                "status_conexao": "ativo" if canal.ativo else "inativo"
            },
            total_atendimentos=metricas.get("atendimentos_hoje", 0),
            atendimentos_ativos=metricas.get("atendimentos_ativos", 0)
        )
        
        return ZigResponse(
            codigo=0,
            mensagem="Canal encontrado",
            dados=canal_detalhado
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{canal_id}",
    response_model=ZigResponse[CanalResponse],
    summary="Atualizar canal",
    description="Atualiza parcialmente os dados de um canal."
)
async def atualizar_canal(
    canal_id: int,
    canal_data: CanalUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Atualiza um canal existente.
    
    Apenas campos fornecidos serão atualizados (PATCH).
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        canal = service.atualizar_canal(canal_id, cliente_id, canal_data)
        
        return ZigResponse(
            codigo=0,
            mensagem="Canal atualizado com sucesso",
            dados=canal
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{canal_id}",
    response_model=ZigResponse[bool],
    summary="Deletar canal",
    description="Remove um canal (apenas se não houver atendimentos ativos)."
)
async def deletar_canal(
    canal_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Deleta um canal.
    
    Só é permitido deletar canais sem atendimentos ativos.
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        sucesso = service.deletar_canal(canal_id, cliente_id)
        
        return ZigResponse(
            codigo=0,
            mensagem="Canal deletado com sucesso",
            dados=sucesso
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==============================================================================
# ENDPOINTS DE MÉTRICAS
# ==============================================================================

@router.get(
    "/{canal_id}/metricas",
    response_model=ZigResponse[CanalMetricasResumo],
    summary="Métricas do canal",
    description="Retorna métricas detalhadas de uso do canal."
)
async def obter_metricas(
    canal_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Obtém métricas de uso do canal.
    
    Inclui:
    - Atendimentos hoje
    - Atendimentos ativos
    - Mensagens enviadas/recebidas hoje
    - Status de conexão
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        metricas = service.obter_metricas_canal(canal_id, cliente_id)
        
        return ZigResponse(
            codigo=0,
            mensagem="Métricas obtidas com sucesso",
            dados=CanalMetricasResumo(**metricas)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter métricas do canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/resumo/faturamento",
    response_model=ZigResponse[dict],
    summary="Resumo para faturamento",
    description="Retorna contagem de canais por tipo para cálculo de mensalidade."
)
async def resumo_faturamento(
    db: Session = Depends(get_db),
    current_user: UsuarioAuth = Depends(get_current_user)
):
    """
    Retorna resumo de canais para faturamento.
    
    Útil para calcular mensalidade baseada em:
    - Quantidade de canais WhatsApp
    - Quantidade de canais Telegram
    - Quantidade de canais VoIP
    - Etc.
    """
    try:
        service = CanalService(db)
        
        cliente_id = current_user.cliente_id or current_user.empresa_id
        
        contagem = service.contar_canais_por_tipo(cliente_id)
        
        return ZigResponse(
            codigo=0,
            mensagem="Resumo de faturamento obtido",
            dados={
                "total_canais": sum(contagem.values()),
                "por_tipo": contagem
            }
        )
    
    except Exception as e:
        logger.error(f"Erro ao obter resumo de faturamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )