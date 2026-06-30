from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.atendimento_service import AtendimentoService

router = APIRouter()


class ZigResponse(BaseModel):
    codigo: int
    erro: Optional[str] = None
    dados: dict = {}


@router.get("/listar", response_model=ZigResponse)
def listar_atendimentos(
    id: Optional[int] = Query(None, description="Código do atendimento"),
    canal: Optional[int] = Query(None, description="1=WhatsApp, 2=Interno"),
    ativo: Optional[str] = Query(None, description="S=Ativo, N=Inativo"),
    data_criacao_inicio: Optional[str] = Query(None, example="2026-01-01"),
    data_criacao_fim: Optional[str] = Query(None, example="2026-01-30"),
    tipo: Optional[int] = Query(None, description="1=automático, 2=manual"),
    departamento_id: Optional[int] = Query(None),
    atendente_usuario_id: Optional[int] = Query(None),
    cliente_id: Optional[int] = Query(None),
    protocolo: Optional[str] = Query(None),
    conexao_id: Optional[int] = Query(None),
    limit: int = Query(10, le=50),
    page: int = Query(1, ge=1),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    Lista atendimentos de forma paginada com múltiplos filtros.
    Contrato compatível com ZigChat GET /atendimento/listar.
    """
    try:
        resultado = AtendimentoService.listar(
            db=db,
            id=id,
            canal=canal,
            ativo=ativo,
            data_criacao_inicio=data_criacao_inicio,
            data_criacao_fim=data_criacao_fim,
            tipo=tipo,
            departamento_id=departamento_id,
            atendente_usuario_id=atendente_usuario_id,
            cliente_id=cliente_id,
            protocolo=protocolo,
            conexao_id=conexao_id,
            limit=limit,
            page=page,
            order=order,
        )

        registros = [
            {
                "id": a.id,
                "protocolo": a.protocolo,
                "telefone": a.telefone,
                "nome_contato": a.nome_contato,
                "canal": a.canal,
                "tipo": a.tipo,
                "ativo": a.ativo,
                "status": a.status,
                "departamento_id": a.departamento_id,
                "usuario_id": a.usuario_id,
                "cliente_id": a.cliente_id,
                "conexao_id": a.conexao_id,
                "criado_em": a.criado_em.isoformat() if a.criado_em else None,
                "atualizado_em": a.atualizado_em.isoformat() if a.atualizado_em else None,
            }
            for a in resultado["registros"]
        ]

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
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


class TransferirAtendimentoRequest(BaseModel):
    atendimento_id: int
    departamento_id: Optional[int] = None
    atendente_usuario_id: Optional[int] = None


@router.post("/transferir", response_model=ZigResponse)
def transferir_atendimento(body: TransferirAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Transfere o atendimento para um departamento e/ou atendente.
    Contrato compatível com ZigChat POST /atendimento/transferir.
    """
    try:
        if body.departamento_id is None and body.atendente_usuario_id is None:
            return ZigResponse(codigo=1, erro="Informe ao menos departamento_id ou atendente_usuario_id.")

        atendimento = AtendimentoService.transferir(
            db=db,
            atendimento_id=body.atendimento_id,
            departamento_id=body.departamento_id,
            atendente_usuario_id=body.atendente_usuario_id,
        )
        if not atendimento:
            return ZigResponse(codigo=1, erro=f"Atendimento {body.atendimento_id} não encontrado.")

        return ZigResponse(
            codigo=0,
            dados={
                "atendimento_id": atendimento.id,
                "status": atendimento.status,
                "departamento_id": atendimento.departamento_id,
                "usuario_id": atendimento.usuario_id,
            },
        )
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


class EncerrarAtendimentoRequest(BaseModel):
    atendimento_id: int
    mensagem: Optional[str] = None


@router.post("/encerrar", response_model=ZigResponse)
async def encerrar_atendimento(body: EncerrarAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Encerra um atendimento, alterando seu status para 'finalizado'.
    Se mensagem informada, envia via Evolution API antes de encerrar.
    Contrato compatível com ZigChat POST /atendimento/encerrar.
    """
    try:
        atendimento = AtendimentoService.buscar_por_id(db, body.atendimento_id)
        if not atendimento:
            return ZigResponse(codigo=1, erro=f"Atendimento {body.atendimento_id} não encontrado.")

        if body.mensagem and atendimento.canal and atendimento.telefone:
            from app.services import evolution_service
            await evolution_service.enviar_texto(
                instance=atendimento.canal.nome,
                number=atendimento.telefone,
                text=body.mensagem,
            )

        encerrado = AtendimentoService.encerrar(db, body.atendimento_id)
        return ZigResponse(
            codigo=0,
            dados={
                "atendimento_id": encerrado.id,
                "status": encerrado.status,
            },
        )
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.get("/context/{atendimentoID}/{context_key}", response_model=ZigResponse)
def consultar_context(atendimentoID: int, context_key: str, db: Session = Depends(get_db)):
    """
    Consulta um contexto do atendimento pela context_key.
    Contrato compatível com ZigChat GET /atendimento/context/{atendimentoID}/{context_key}.
    """
    try:
        ctx = AtendimentoService.buscar_context(db, atendimentoID, context_key)
        if not ctx:
            return ZigResponse(codigo=1, erro="Contexto não encontrado.")
        return ZigResponse(
            codigo=0,
            dados={
                "id": ctx.id,
                "atendimento_id": ctx.atendimento_id,
                "context_key": ctx.context_key,
                "value": ctx.value,
            },
        )
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


class DeletarContextRequest(BaseModel):
    atendimento_id: int
    context_key: str


@router.post("/deletarContext", response_model=ZigResponse)
def deletar_context(body: DeletarContextRequest, db: Session = Depends(get_db)):
    """
    Deleta um contexto do atendimento pela context_key.
    Contrato compatível com ZigChat POST /atendimento/deletarContext.
    """
    try:
        removido = AtendimentoService.deletar_context(
            db=db,
            atendimento_id=body.atendimento_id,
            context_key=body.context_key,
        )
        if not removido:
            return ZigResponse(codigo=1, erro="Contexto não encontrado.")
        return ZigResponse(codigo=0, dados={"removido": True})
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


class CriarAlteraContextRequest(BaseModel):
    atendimento_id: int
    context_key: str
    value: Any          # aceita string JSON ou objeto


@router.post("/criarAlteraContext", response_model=ZigResponse)
def criar_altera_context(body: CriarAlteraContextRequest, db: Session = Depends(get_db)):
    """
    Adiciona ou atualiza um contexto no atendimento.
    Se a context_key já existir, sobrescreve o value.
    Contrato compatível com ZigChat POST /atendimento/criarAlteraContext.
    """
    try:
        value_str = body.value if isinstance(body.value, str) else str(body.value)

        ctx = AtendimentoService.criar_altera_context(
            db=db,
            atendimento_id=body.atendimento_id,
            context_key=body.context_key,
            value=value_str,
        )

        if not ctx:
            return ZigResponse(codigo=1, erro=f"Atendimento {body.atendimento_id} não encontrado.")

        return ZigResponse(
            codigo=0,
            dados={
                "id": ctx.id,
                "atendimento_id": ctx.atendimento_id,
                "context_key": ctx.context_key,
                "value": ctx.value,
            },
        )

    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))
