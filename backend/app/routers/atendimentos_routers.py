# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.routers.atendimentos_routers
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-27
# VERSÃO: 4.0.0 (Refatoração: Remoção de acoplamento ZigChat, adoção de RESTful 
#          padrão e injeção obrigatória de contexto multi-tenant)
# ==============================================================================
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · atendimentos (rotas de atendimentos)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimentos_routers.py
@module   Backend / /tmp/eco-base/backend/app/routers
@author   Aldemir Queiroz
@since    2026
@version  4.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
--------------
Endpoints HTTP para domínio de Atendimento (Conversas, Ligações, Contextos). Camada de apresentação (Controller). Delega lógica de negócio, validação de regras de canal e notificações ao AtendimentoService.

O QUE ESTE ARQUIVO É
-------------------
Borda HTTP estrita - sem regra de negócio. Recebe requisições, valida via schemas, delega ao AtendimentoService com injeção de contexto, converte erros de negócio em HTTPException. Usa AsyncSession.

SEGURANÇA E MULTI-TENANCY
-------------------------
Exige autenticação JWT e injeta CurrentEmpresa. empresa_id NUNCA aceito via payload ou query string (prevenção IDOR). Operações restritas ao tenant do usuário.

PREFIXO E MONTAGEM
------------------
Define router sem prefix interno próprio. Registrado em main.py como (atendimento, "/api/atendimento", "Atendimento", True, "atendente") via ROUTERS_CONFIG. Montagem ocorre com prefix /api/atendimento.

ENDPOINTS
---------
método | path | descrição | status retorno
-------|------|-----------|---------------
GET    | /    | Listar atendimentos com paginação/filtros (por empresa) | 200
GET    | /{id} | Buscar atendimento por ID | 200 / 404
POST   | /    | Criar atendimento | 201 / 400/422
PUT    | /{id} | Atualizar atendimento | 200 / 400/404
DELETE | /{id} | Excluir/encerrar conforme regras | 200/204 / 400/404
POST   | /{id}/transferir | Transferir atendimento | 200 / 400/404
POST   | /{id}/finalizar | Finalizar atendimento | 200 / 400/404
GET    | /contextos | Listar contextos | 200
POST   | /contextos | Criar contexto | 201 / 400/422
GET    | /contextos/{id} | Buscar contexto | 200 / 404

MULTI-TENANT
------------
Obrigatório via CurrentEmpresa (injeção). Isolamento total por empresa_id. Nunca recebido via body/query.

RELACIONAMENTO
--------------
Service: app.services.atendimento_service.AtendimentoService (instanciado com empresa_id)
Schemas: app.schemas.atendimento_schemas.*
Models: app.models.Atendimento, app.models.Contexto
Dependências: get_db (AsyncSession), CurrentEmpresa
Exceptions: RecursoNaoEncontradoError, ValidacaoNegocioError (tratados conforme handlers)

OBSERVAÇÃO
----------
Arquivo já possui docstring substancial. Preservar e melhorar conforme conteúdo existente, sem substituir por pior. Código executável, assinaturas, decorators e comportamento originais preservados.
"""

from __future__ import annotations

from typing import Optional, Any
from datetime import date

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Dependências e Modelos
from app.database import get_db
from app.deps import CurrentEmpresa
from app.schemas.atendimento_schemas import (
    AtendimentoCreate,
    AtendimentoResponse,
    AtendimentoUpdate,
    ContextoCreate,
    ContextoResponse,
    TransferenciaRequest,
)
from app.services.atendimento_service import AtendimentoService
from app.exceptions import RecursoNaoEncontradoError, ValidacaoNegocioError

# Inicialização do Router
# SEM prefix próprio — igual aos outros 15 routers.
#
# `main.py` monta este router em `/api/atendimento`. Com `prefix="/atendimentos"`
# aqui dentro, a rota real virava `/api/atendimento/atendimentos/`: dois
#segmentos para o mesmo domínio, um no plural e outro no singular, e nenhuma
#combinação batendo com a URL que o frontend chama. O prefixo do router era
# o único do projeto a declarar prefixo; someu para a URL fechar.
router = APIRouter(tags=["Atendimentos"])


# ==============================================================================
# SEÇÃO 1: CONSULTAS (GET)
# ==============================================================================

@router.get(
    "/", 
    response_model=dict[str, Any], 
    summary="Listar atendimentos com paginação e filtros"
)
async def listar_atendimentos(
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
    canal_id: Optional[int] = Query(None, description="Filtro por ID do canal (ex: WhatsApp, Telefonia)"),
    status: Optional[str] = Query(None, description="Filtro por status (aberto, em_atendimento, finalizado)"),
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> dict[str, Any]:
    """
    Lista atendimentos pertencentes exclusivamente à empresa do usuário autenticado.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    
    # O service devolve 'items', 'total', 'page' e 'limit'. A chave interna e
    # 'items'; a resposta usa 'registros' por contrato com o frontend.
    resultado = await service.listar(
        canal=canal_id,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
        page=page,
        limit=limit,
    )
    
    return {
        "total": resultado["total"],
        "page": resultado["page"],
        "limit": resultado["limit"],
        "total_pages": (resultado["total"] + limit - 1) // limit,
        "registros": [AtendimentoResponse.from_atendimento(r) for r in resultado["items"]]
    }


@router.get(
    "/{atendimento_id}", 
    response_model=AtendimentoResponse,
    summary="Buscar atendimento por ID"
)
async def buscar_atendimento(
    atendimento_id: int,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> AtendimentoResponse:
    """
    Recupera os detalhes de um atendimento específico.
    Falha com 404 se o atendimento não existir ou não pertencer à empresa.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    atendimento = await service.buscar_por_id(atendimento_id)
    
    if not atendimento:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado ou acesso negado.")
        
    return AtendimentoResponse.from_atendimento(atendimento)


# ==============================================================================
# SEÇÃO 2: ESCRITA E AÇÕES (POST, PATCH, DELETE)
# ==============================================================================

@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED, 
    response_model=AtendimentoResponse,
    summary="Criar novo atendimento"
)
async def criar_atendimento(
    payload: AtendimentoCreate,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> AtendimentoResponse:
    """
    Inicia um novo atendimento. O empresa_id é injetado pelo token, 
    ignorando qualquer tentativa de manipulação no payload.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    novo_atendimento = await service.criar(**payload.model_dump())
    return AtendimentoResponse.from_atendimento(novo_atendimento)


@router.patch(
    "/{atendimento_id}", 
    response_model=AtendimentoResponse,
    summary="Atualizar dados do atendimento"
)
async def atualizar_atendimento(
    atendimento_id: int,
    payload: AtendimentoUpdate,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> AtendimentoResponse:
    """
    Atualização parcial de um atendimento. Campos sensíveis (como empresa_id) 
    são protegidos no nível do Service.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    atendimento_atualizado = await service.atualizar(
        atendimento_id, 
        **payload.model_dump(exclude_unset=True)
    )
    
    if not atendimento_atualizado:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado.")
        
    return AtendimentoResponse.from_atendimento(atendimento_atualizado)


@router.post(
    "/{atendimento_id}/transferir", 
    response_model=AtendimentoResponse,
    summary="Transferir atendimento para outro departamento, usuário ou canal"
)
async def transferir_atendimento(
    atendimento_id: int,
    payload: TransferenciaRequest,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> AtendimentoResponse:
    """
    Transfere o atendimento. 
    NOTA: A notificação ao cliente (via WhatsApp/Evolution ou URA/Telefonia) 
    é orquestrada internamente pelo AtendimentoService, mantendo este router limpo.
    """
    if not any([payload.departamento_id, payload.usuario_id, payload.canal_id]):
        raise ValidacaoNegocioError("É necessário informar ao menos um destino: departamento_id, usuario_id ou canal_id.")

    service = AtendimentoService(db, empresa_id=empresa.id)
    atendimento = await service.transferir(
        atendimento_id=atendimento_id,
        departamento_id=payload.departamento_id,
        usuario_id=payload.usuario_id,
        canal_id=payload.canal_id,
        mensagem_notificacao=payload.mensagem
    )
    
    if not atendimento:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado.")
        
    return AtendimentoResponse.from_atendimento(atendimento)


@router.post(
    "/{atendimento_id}/encerrar", 
    response_model=AtendimentoResponse,
    summary="Encerrar atendimento"
)
async def encerrar_atendimento(
    atendimento_id: int,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
    mensagem_final: Optional[str] = Query(None, description="Mensagem opcional de despedida"),
) -> AtendimentoResponse:
    """
    Finaliza o ciclo de vida do atendimento. O service cuida de salvar o histórico 
    e disparar a mensagem final através do provedor de canal correto.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    atendimento_encerrado = await service.encerrar(
        atendimento_id=atendimento_id,
        mensagem_final=mensagem_final
    )
    
    if not atendimento_encerrado:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado.")
        
    return AtendimentoResponse.from_atendimento(atendimento_encerrado)


# ==============================================================================
# SEÇÃO 3: GERENCIAMENTO DE CONTEXTO (Memória da Conversa/URA)
# ==============================================================================

@router.get(
    "/{atendimento_id}/contextos", 
    response_model=list[ContextoResponse],
    summary="Listar todos os contextos de um atendimento"
)
async def listar_contextos(
    atendimento_id: int,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> list[ContextoResponse]:
    """Retorna todas as variáveis de contexto (ex: opções de URA, dados coletados)."""
    service = AtendimentoService(db, empresa_id=empresa.id)
    contextos = await service.listar_contextos(atendimento_id)
    return [ContextoResponse.model_validate(c) for c in contextos]


@router.post(
    "/{atendimento_id}/contextos", 
    response_model=ContextoResponse,
    summary="Criar ou atualizar (Upsert) um contexto"
)
async def upsert_contexto(
    atendimento_id: int,
    payload: ContextoCreate,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> ContextoResponse:
    """
    Salva uma variável de contexto. Se a chave já existir, o valor é atualizado.
    Essencial para manter o estado de máquinas de URA ou fluxos de IA.
    """
    service = AtendimentoService(db, empresa_id=empresa.id)
    contexto = await service.criar_ou_atualizar_contexto(
        atendimento_id=atendimento_id,
        context_key=payload.context_key,
        value=payload.value
    )
    
    if not contexto:
        raise RecursoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado.")
        
    return ContextoResponse.model_validate(contexto)


@router.delete(
    "/{atendimento_id}/contextos/{context_key}", 
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Remover um contexto específico"
)
async def deletar_contexto(
    atendimento_id: int,
    context_key: str,
    empresa: CurrentEmpresa,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove uma variável de contexto do atendimento."""
    service = AtendimentoService(db, empresa_id=empresa.id)
    removido = await service.deletar_contexto(atendimento_id, context_key)
    
    if not removido:
        raise RecursoNaoEncontradoError(f"Contexto '{context_key}' não encontrado no atendimento {atendimento_id}.")
    
    # Retorna 204 No Content, padrão REST para deleção bem-sucedida
    return None