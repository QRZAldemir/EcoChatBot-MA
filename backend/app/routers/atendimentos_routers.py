# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# Arquivo: atendimento.py (Pasta: app/routers)
# ==============================================================================
# DESCRIÇÃO:
# Este arquivo define as rotas (endpoints) da API responsáveis pelas operações
# de "Atendimento". Atua como camada de apresentação (Router/Controller),
# validando dados de entrada (Pydantic), delegando lógica de negócios para
# AtendimentoService e retornando respostas padronizadas no formato ZigResponse.
#
# CONTRATO:
# As rotas seguem o padrão de integração com o ZigChat (listar, transferir,
# encerrar e gerenciar contextos).
#
# AUTENTICAÇÃO:
# Tratada via middleware JWT no main.py. Todas as rotas deste router exigem
# token Bearer válido. O parâmetro 'db' é injetado via Depends(get_db).
#
# STATUS HTTP:
# O contrato ZigChat exige HTTP 200 em todas as respostas, com o status
# real da operação indicado no campo 'codigo' do body (0=Sucesso, 1=Erro).
# ==============================================================================
import logging
from datetime import date, datetime
from typing import Optional, Any

from app.core.zig_response import ZigResponse
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Importações internas
from app.database import get_db
from app.models import Canal, Departamento
from app.services.atendimento_service import AtendimentoService
from app.exceptions import (
    NegocioException,
    RecursoNaoEncontradoException,
    ValidacaoNegocioException,
)

# Inicialização
router = APIRouter()
logger = logging.getLogger(__name__)


# ==============================================================================
# SEÇÃO 1: MODELOS DE REQUISIÇÃO E RESPOSTA (PYDANTIC SCHEMAS)
# ==============================================================================

class AtendimentoResponse(BaseModel):
    """
    Schema de resposta para atendimentos.

    CORRIGIDO (2026-07-05): Separação de 'canal' em 'tipo_canal' e 'canal_id'
    para evitar conflito com relacionamento ORM.
    """
    id: int
    protocolo: str
    telefone: Optional[str] = None
    nome_contato: Optional[str] = None
    tipo_canal: Optional[int] = None
    canal_id: Optional[int] = None
    tipo: Optional[int] = None
    ativo: Optional[bool] = None
    status: Optional[str] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cliente_id: Optional[int] = None
    conexao_id: Optional[int] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransferirAtendimentoRequest(BaseModel):
    atendimento_id: int
    departamento_id: Optional[int] = None
    atendente_usuario_id: Optional[int] = None
    canal_id: Optional[int] = None
    mensagem: Optional[str] = None


class EncerrarAtendimentoRequest(BaseModel):
    atendimento_id: int
    mensagem: Optional[str] = None


class DeletarContextRequest(BaseModel):
    atendimento_id: int
    context_key: str


class CriarAlteraContextRequest(BaseModel):
    atendimento_id: int
    context_key: str
    value: Any


# ==============================================================================
# SEÇÃO 2: ROTAS DE LEITURA / CONSULTA (GET)
# ==============================================================================

@router.get("/listar", response_model=ZigResponse)
def listar_atendimentos(
    id: Optional[int] = Query(None, description="Código do atendimento"),
    canal: Optional[int] = Query(None, description="1=WhatsApp, 2=Interno"),
    ativo: Optional[str] = Query(None, description="S=Ativo, N=Inativo"),
    # MELHORIA: Validação de datas no nível do schema (Pydantic rejeita formatos inválidos)
    data_criacao_inicio: Optional[date] = Query(
        None,
        description="Data inicial (YYYY-MM-DD)",
        examples=["2026-01-01"]
    ),
    data_criacao_fim: Optional[date] = Query(
        None,
        description="Data final (YYYY-MM-DD)",
        examples=["2026-01-30"]
    ),
    tipo: Optional[int] = Query(None, description="1=automático, 2=manual"),
    departamento_id: Optional[int] = Query(None),
    atendente_usuario_id: Optional[int] = Query(None),
    cliente_id: Optional[int] = Query(None),
    protocolo: Optional[str] = Query(None),
    conexao_id: Optional[int] = Query(None),
    status: Optional[str] = Query(
        None,
        description="aberto, fila, em_atendimento ou finalizado"
    ),
    limit: int = Query(10, le=50, description="Máximo 50 registros por página"),
    page: int = Query(1, ge=1, description="Página (mínimo 1)"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Ordenação"),
    db: Session = Depends(get_db),
):
    """
    Lista atendimentos de forma paginada com múltiplos filtros.
    """
    try:
        resultado = AtendimentoService.listar(
            db=db, id=id, canal=canal, ativo=ativo,
            data_criacao_inicio=data_criacao_inicio.isoformat() if data_criacao_inicio else None,
            data_criacao_fim=data_criacao_fim.isoformat() if data_criacao_fim else None,
            tipo=tipo, departamento_id=departamento_id,
            atendente_usuario_id=atendente_usuario_id,
            cliente_id=cliente_id, protocolo=protocolo, conexao_id=conexao_id,
            status=status, limit=limit, page=page, order=order,
        )

        registros = [AtendimentoResponse.model_validate(a) for a in resultado["registros"]]

        return ZigResponse(
            codigo=0,
            dados={
                "total": resultado["total"],
                "pagina": resultado["pagina"],
                "limit": resultado["limit"],
                "paginas": resultado["paginas"],
                "registros": registros,
            },
        )
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /listar")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


@router.get("/indicadores", response_model=ZigResponse)
def indicadores_atendimentos(
    data_criacao_inicio: Optional[date] = Query(
        None,
        description="Data inicial (YYYY-MM-DD)",
        examples=["2026-01-01"]
    ),
    data_criacao_fim: Optional[date] = Query(
        None,
        description="Data final (YYYY-MM-DD)",
        examples=["2026-01-30"]
    ),
    db: Session = Depends(get_db),
):
    """
    Indicadores de atendimento em tempo real.
    
    MELHORIA: Validação de intervalo máximo (90 dias) para evitar consultas
    excessivamente custosas.
    """
    try:
        # Validação de intervalo máximo
        if data_criacao_inicio and data_criacao_fim:
            intervalo_dias = (data_criacao_fim - data_criacao_inicio).days
            if intervalo_dias > 90:
                raise ValidacaoNegocioException(
                    f"Intervalo máximo permitido: 90 dias. Solicitado: {intervalo_dias} dias."
                )
            if intervalo_dias < 0:
                raise ValidacaoNegocioException(
                    "Data final não pode ser anterior à data inicial."
                )

        dados = AtendimentoService.indicadores(
            db=db,
            data_criacao_inicio=data_criacao_inicio.isoformat() if data_criacao_inicio else None,
            data_criacao_fim=data_criacao_fim.isoformat() if data_criacao_fim else None,
        )
        return ZigResponse(codigo=0, dados=dados)
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /indicadores")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


@router.get("/context/{atendimentoID}/{context_key}", response_model=ZigResponse)
def consultar_context(atendimentoID: int, context_key: str, db: Session = Depends(get_db)):
    """
    Consulta um contexto do atendimento pela context_key.
    """
    try:
        ctx = AtendimentoService.buscar_context(db, atendimentoID, context_key)
        if not ctx:
            raise RecursoNaoEncontradoException("Contexto não encontrado.")
        
        return ZigResponse(
            codigo=0,
            dados={
                "id": ctx.id,
                "atendimento_id": ctx.atendimento_id,
                "context_key": ctx.context_key,
                "value": ctx.value,
            }
        )
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /context")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


# ==============================================================================
# SEÇÃO 3: ROTAS DE ESCRITA / AÇÃO (POST)
# ==============================================================================

def _buscar_instancia(db: Session, atendimento_id: int) -> Optional[str]:
    """
    Resolve o nome real da instância Evolution de um atendimento.
    """
    ctx = AtendimentoService.buscar_context(db, atendimento_id, "instancia")
    return ctx.value if ctx and ctx.value else None


async def _avisar_cliente_transferencia(db: Session, atendimento, mensagem: Optional[str]) -> None:
    """
    Avisa o cliente por WhatsApp sobre transferência. Falhas são apenas logadas.
    """
    if not atendimento.telefone:
        return

    instancia = _buscar_instancia(db, atendimento.id)
    if not instancia:
        logger.warning(
            "atendimento | transferir | sem 'instancia' para atendimento=%s",
            atendimento.id,
        )
        return

    texto = mensagem
    if not texto:
        setor = None
        if atendimento.canal_id:
            canal = db.query(Canal).filter(Canal.id == atendimento.canal_id).first()
            setor = canal.nome if canal else None
        if not setor and atendimento.departamento_id:
            depto = db.query(Departamento).filter(Departamento.id == atendimento.departamento_id).first()
            setor = depto.nome if depto else None

        texto = (
            f"🔄 Você foi transferido(a) para o setor de *{setor}*. "
            "Em instantes, um de nossos atendentes continuará seu atendimento."
            if setor else
            "🔄 Você foi transferido(a) para outro atendente. Em instantes, continuaremos seu atendimento."
        )

    try:
        from app.services import evolution_service
        await evolution_service.enviar_texto(
            instance=instancia, number=atendimento.telefone, text=texto,
        )
    except Exception:
        logger.exception("atendimento | transferir | falha ao avisar paciente")


@router.post("/transferir", response_model=ZigResponse)
async def transferir_atendimento(body: TransferirAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Transfere o atendimento e avisa o paciente por WhatsApp.
    """
    try:
        if body.departamento_id is None and body.atendente_usuario_id is None and body.canal_id is None:
            raise ValidacaoNegocioException(
                "Informe ao menos departamento_id, atendente_usuario_id ou canal_id."
            )

        atendimento = AtendimentoService.transferir(
            db=db,
            atendimento_id=body.atendimento_id,
            departamento_id=body.departamento_id,
            atendente_usuario_id=body.atendente_usuario_id,
            canal_id=body.canal_id,
        )
        
        if not atendimento:
            raise RecursoNaoEncontradoException(
                f"Atendimento {body.atendimento_id} não encontrado."
            )

        await _avisar_cliente_transferencia(db, atendimento, body.mensagem)

        return ZigResponse(
            codigo=0,
            dados={
                "atendimento_id": atendimento.id,
                "status": atendimento.status,
                "departamento_id": atendimento.departamento_id,
                "usuario_id": atendimento.usuario_id,
                "canal_id": atendimento.canal_id,
            },
        )
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /transferir")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


@router.post("/encerrar", response_model=ZigResponse)
async def encerrar_atendimento(body: EncerrarAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Encerra um atendimento, enviando mensagem final se informada.
    """
    try:
        atendimento = AtendimentoService.buscar_por_id(db, body.atendimento_id)
        if not atendimento:
            raise RecursoNaoEncontradoException(
                f"Atendimento {body.atendimento_id} não encontrado."
            )

        if body.mensagem and atendimento.telefone:
            instancia = _buscar_instancia(db, atendimento.id)
            if instancia:
                try:
                    from app.services import evolution_service
                    await evolution_service.enviar_texto(
                        instance=instancia,
                        number=atendimento.telefone,
                        text=body.mensagem,
                    )
                except Exception:
                    logger.exception("atendimento | encerrar | falha ao enviar mensagem final")
            else:
                logger.warning(
                    "atendimento | encerrar | sem 'instancia' para atendimento=%s",
                    atendimento.id,
                )

        encerrado = AtendimentoService.encerrar(db, body.atendimento_id)
        return ZigResponse(
            codigo=0,
            dados={
                "atendimento_id": encerrado.id,
                "status": encerrado.status,
            },
        )
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /encerrar")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


@router.post("/deletarContext", response_model=ZigResponse)
def deletar_context(body: DeletarContextRequest, db: Session = Depends(get_db)):
    """
    Deleta um contexto do atendimento.
    """
    try:
        removido = AtendimentoService.deletar_context(
            db=db, atendimento_id=body.atendimento_id, context_key=body.context_key,
        )
        if not removido:
            raise RecursoNaoEncontradoException("Contexto não encontrado.")
            
        return ZigResponse(codigo=0, dados={"removido": True})
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /deletarContext")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")


@router.post("/criarAlteraContext", response_model=ZigResponse)
def criar_altera_context(body: CriarAlteraContextRequest, db: Session = Depends(get_db)):
    """
    Adiciona ou atualiza um contexto no atendimento (Upsert).
    """
    try:
        value_str = body.value if isinstance(body.value, str) else str(body.value)

        ctx = AtendimentoService.criar_altera_context(
            db=db, atendimento_id=body.atendimento_id,
            context_key=body.context_key, value=value_str,
        )

        if not ctx:
            raise RecursoNaoEncontradoException(
                f"Atendimento {body.atendimento_id} não encontrado."
            )

        return ZigResponse(
            codigo=0,
            dados={
                "id": ctx.id,
                "atendimento_id": ctx.atendimento_id,
                "context_key": ctx.context_key,
                "value": ctx.value,
            },
        )
    except NegocioException as e:
        return ZigResponse(codigo=1, erro=e.mensagem)
    except Exception:
        logger.exception("Erro inesperado em /criarAlteraContext")
        return ZigResponse(codigo=1, erro="Erro interno do servidor.")