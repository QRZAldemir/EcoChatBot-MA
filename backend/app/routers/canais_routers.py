"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · canais_routers
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canais_routers.py
@module   Backend / App / Routers / canais_routers
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Camada HTTP dos canais contratados: o CRUD, as métricas por canal e o
resumo de faturamento. É o arquivo que o frontend chama quando o gestor
administra os números da empresa.

O QUE ESTE ARQUIVO É
───────────────────
A borda da API. Recebe JSON, valida formato, chama o service e devolve
JSON. NÃO tem regra de negócio aqui — se uma condição de negócio entrar
neste arquivo, ela está no lugar errado.

    endpoint  ──►  valida formato  ──►  service (regras)  ──►  model

O OBJETO
────────
Não há uma classe de domínio aqui. O objeto deste arquivo é o
`APIRouter` em `router`: um agrupador de rotas que `main.py` monta em
`/api/canais`. Os objetos de entrada e saída são `CanalCreate`,
`CanalUpdate` e `CanalResponse` (de `app/schemas/canal_schemas.py`).

    Exemplo do que é e do que NÃO é a responsabilidade dele:

        "o apelido tem pelo menos 3 caracteres"   →  schema (aqui: valida)
        "esse canal já existe para este telefone" →  service (aqui: NÃO)

ENDPOINTS
─────────
    POST   /api/canais                     cria um canal contratado
    GET    /api/canais                     lista com filtros e paginação
    GET    /api/canais/{id}                detalhe de um canal
    PUT    /api/canais/{id}                atualiza
    DELETE /api/canais/{id}                remove (soft delete)
    GET    /api/canais/{id}/metricas       mensagens e taxa de resposta
    GET    /api/canais/resumo-faturamento  mensalidade e uso por canal

CONTRATO DE RESPOSTA
────────────────────
Todas as rotas de sucesso devolvem `SuccessResponse`, definido em
`app/schemas/response_schemas.py`. É o formato nativo do projeto — não
existe mais o envelope `{ codigo, dados }` que o frontend usava antes.

Erros NÃO usam `SuccessResponse`: são `ErrorResponse` do mesmo módulo,
com o status HTTP correspondente (404 para inexistente, 403 para tenant
errado, 409 para conflito de unicidade). Um erro devolvido com HTTP 200
e `codigo: 1` no corpo faz o `try/except` do Angular não disparar e o
usuário vê "sucesso" com a tela vazia.

ISOLAMENTO MULTI-TENANT
────────────────────────
`empresa_id` NUNCA vem do corpo da requisição. Vem de
`deps.CurrentEmpresa`, que lê o token. Um cliente que edite o JSON para
trocar o `empresa_id` não muda nada — o valor do corpo é ignorado.

RELACIONAMENTO
──────────────
    ┌──────────────────────────────────────────────────────────────────┐
    │ main.py  monta em /api/canais                                   │
    │   └─► canais_routers        você está aqui                      │
    │         └─► CanalService    unicidade, credenciais, tenant      │
    │               └─► CanalContratado (model)                       │
    └──────────────────────────────────────────────────────────────────┘
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Empresa
from app.schemas.canal_schemas import (
    CanalContratadoCreate,
    CanalContratadoUpdate,
    CanalContratadoResponse,
    CanalContratadoDetalhado,
    CanalListaResponse,
    CanalMetricasResumo,
)
from app.services.canal_service import CanalService
from app.deps import get_current_empresa
from app.schemas.response_schemas import SuccessResponse

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
    response_model=SuccessResponse[CanalContratadoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo canal",
    description="Cria um novo canal de comunicação para a empresa do usuário autenticado."
)
async def criar_canal(
    canal_data: CanalContratadoCreate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
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
        
        # A dependencia `get_current_empresa` já devolve a empresa validada
        # (403 se o usuário não tiver empresa ativa), então aqui não há o que
        # checar: só usar.
        empresa_id = empresa.id

        canal = await service.criar_canal(canal_data, empresa_id)
        
        return SuccessResponse(
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
    response_model=SuccessResponse[CanalListaResponse],
    summary="Listar canais",
    description="Lista todos os canais da empresa com paginação e filtros."
)
async def listar_canais(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(50, ge=1, le=100, description="Limite por página"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status"),
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
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
        
        empresa_id = empresa.id
        
        canais, total = await service.listar_canais(
            empresa_id=empresa_id,
            page=page,
            limit=limit,
            tipo=tipo,
            ativo=ativo
        )
        
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return SuccessResponse(
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
    response_model=SuccessResponse[CanalContratadoDetalhado],
    summary="Buscar canal por ID",
    description="Retorna dados detalhados de um canal específico."
)
async def buscar_canal(
    canal_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
):
    """
    Busca um canal específico por ID.
    
    Retorna dados completos incluindo métricas de uso.
    """
    try:
        service = CanalService(db)
        
        empresa_id = empresa.id
        
        canal = await service.buscar_por_id(canal_id, empresa_id)
        
        # Obter métricas
        metricas = await service.obter_metricas_canal(canal_id, empresa_id)
        
        # O mapeamento campo-a-campo foi removido de propósito: ele citava
        # 8 colunas que não existem mais no model (nome, descricao,
        # identificador, configuracao_json, departamento_id,
        # webhook_verify_token, ultimo_sync, cliente_id) e ia quebrar de novo
        # na próxima mudança. `model_validate` lê direto do model, e a
        # ofuscação de `credenciais` continua valendo porque é o schema que
        # aplica.
        canal_detalhado = CanalContratadoDetalhado.model_validate(
            {**canal.__dict__, "status_conexao": "ativo" if canal.ativo else "inativo"},
            update={
                "total_atendimentos": metricas.get("atendimentos_hoje", 0),
                "atendimentos_ativos": metricas.get("atendimentos_ativos", 0),
                "ultima_mensagem": None,
            },
        )
        
        return SuccessResponse(
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
    response_model=SuccessResponse[CanalContratadoResponse],
    summary="Atualizar canal",
    description="Atualiza parcialmente os dados de um canal."
)
async def atualizar_canal(
    canal_id: int,
    canal_data: CanalContratadoUpdate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
):
    """
    Atualiza um canal existente.
    
    Apenas campos fornecidos serão atualizados (PATCH).
    """
    try:
        service = CanalService(db)
        
        empresa_id = empresa.id
        
        canal = await service.atualizar_canal(canal_id, empresa_id, canal_data)
        
        return SuccessResponse(
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
    response_model=SuccessResponse[bool],
    summary="Deletar canal",
    description="Remove um canal (apenas se não houver atendimentos ativos)."
)
async def deletar_canal(
    canal_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
):
    """
    Deleta um canal.
    
    Só é permitido deletar canais sem atendimentos ativos.
    """
    try:
        service = CanalService(db)
        
        empresa_id = empresa.id
        
        sucesso = await service.deletar_canal(canal_id, empresa_id)
        
        return SuccessResponse(
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
    response_model=SuccessResponse[CanalMetricasResumo],
    summary="Métricas do canal",
    description="Retorna métricas detalhadas de uso do canal."
)
async def obter_metricas(
    canal_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
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
        
        empresa_id = empresa.id
        
        metricas = await service.obter_metricas_canal(canal_id, empresa_id)
        
        return SuccessResponse(
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
    response_model=SuccessResponse[dict],
    summary="Resumo para faturamento",
    description="Retorna contagem de canais por tipo para cálculo de mensalidade."
)
async def resumo_faturamento(
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa)
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
        
        empresa_id = empresa.id
        
        contagem = await service.contar_canais_por_tipo(empresa_id)
        
        return SuccessResponse(
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