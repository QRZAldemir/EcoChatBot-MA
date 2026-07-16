# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# ==============================================================================
# Arquivo: atendimento.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Este arquivo define as rotas (endpoints) da API responsáveis pelas operações
# de "Atendimento". Ele atua como a camada de apresentação (Router/Controller),
# recebendo as requisições HTTP, validando os dados de entrada (via Pydantic),
# delegando a lógica de negócios para a camada de Service (AtendimentoService)
# e retornando as respostas padronizadas no formato ZigResponse.
#
# CONTRATO:
# As rotas seguem o padrão de integração com o ZigChat (listar, transferir,
# encerrar e gerenciar contextos).
# ==============================================================================
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

# Importações internas do projeto
from app.database import get_db
from app.models import Canal, Departamento
from app.services.atendimento_service import AtendimentoService

# Inicializa o roteador do FastAPI. 
# Todas as rotas definidas aqui serão registradas sob um prefixo no arquivo main.py
router = APIRouter()
logger = logging.getLogger(__name__)


# ==============================================================================
# SEÇÃO 1: MODELOS DE REQUISIÇÃO E RESPOSTA (PYDANTIC SCHEMAS)
# ==============================================================================
# Por que usar esta seção? Em vez de criar dicionários manualmente (o que gera 
# código duplicado e propenso a erros), usamos Schemas do Pydantic. Eles garantem
# a validação automática dos dados que entram (Request) e formatam os dados que 
# saem da API (Response), além de gerarem a documentação automática (Swagger/Redoc).

# Modelo padrão de resposta da API (Compatível com ZigChat)
class ZigResponse(BaseModel):
    codigo: int              # 0 = Sucesso, 1 = Erro
    erro: Optional[str] = None
    dados: dict = {}

# Modelo de resposta para um Atendimento individual.
# MELHORIA PRINCIPAL: Com "from_attributes = True", o Pydantic consegue ler os
# dados diretamente do objeto do Banco de Dados (SQLAlchemy), eliminando a
# necessidade de fazer aquele mapeamento manual campo a campo (dicionário).
class AtendimentoResponse(BaseModel):
    """
    Schema de resposta para atendimentos.

    ==================================================================
    CORRIGIDO (2026-07-05): Resolução de conflito de tipos
    ==================================================================
    Anteriormente, 'canal' poderia ser:
    - int (tipo: 1=WhatsApp, 2=Interno)
    - object (relacionamento com tabela canais)

    Solução: Separar em dois campos:
    - tipo_canal: int (tipo do canal)
    - canal_id: int (foreign key para canais)

    O relacionamento ORM (atendimento.canal) continua acessível no
    código Python, mas não é exposto no JSON da API.
    ==================================================================
    """
    id: int
    protocolo: str
    telefone: Optional[str] = None
    nome_contato: Optional[str] = None

    # Tipo de canal: 1=WhatsApp, 2=Interno
    # CORRIGIDO: Renomeado de 'canal' para evitar conflito com relacionamento ORM
    tipo_canal: Optional[int] = None

    # ID do canal relacionado (foreign key para tabela 'canais')
    # Adicionado para acesso explícito ao canal via API
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
        from_attributes = True # Permite ler diretamente dos modelos ORM

# Modelos de Requisição (Request Bodies) para as rotas POST
# Garantem que o cliente da API envie exatamente os campos necessários
class TransferirAtendimentoRequest(BaseModel):
    atendimento_id: int
    departamento_id: Optional[int] = None
    atendente_usuario_id: Optional[int] = None
    canal_id: Optional[int] = None
    mensagem: Optional[str] = None   # texto customizado avisando o paciente; se omitido, usa um padrão

class EncerrarAtendimentoRequest(BaseModel):
    atendimento_id: int
    mensagem: Optional[str] = None

class DeletarContextRequest(BaseModel):
    atendimento_id: int
    context_key: str

class CriarAlteraContextRequest(BaseModel):
    atendimento_id: int
    context_key: str
    value: Any  # Aceita string JSON ou objeto, será convertido para string depois


# ==============================================================================
# SEÇÃO 2: ROTAS DE LEITURA / CONSULTA (GET)
# ==============================================================================
# Rotas responsáveis por buscar dados no sistema sem alterar o estado do servidor.

@router.get("/listar", response_model=ZigResponse)
def listar_atendimentos(
    # Definição dos parâmetros de Query (enviados via URL: ?id=1&canal=2)
    # O FastAPI usa isso para validar os tipos e gerar a documentação interativa
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
    # Extensão própria deste projeto (fora do contrato ZigChat) — permite ao
    # painel do atendente pedir só "fila" ou só "em_atendimento" em vez de
    # filtrar status no cliente depois de baixar tudo.
    status: Optional[str] = Query(None, description="aberto, fila, em_atendimento ou finalizado"),
    # Parâmetros de paginação e ordenação com validações embutidas
    limit: int = Query(10, le=50),  # le=50 limita o máximo a 50 por página
    page: int = Query(1, ge=1),     # ge=1 garante que a página seja pelo menos 1
    order: str = Query("desc", pattern="^(asc|desc)$"), # Regex: só aceita 'asc' ou 'desc'
    # Injeção de dependência: O FastAPI gera e injeta uma sessão do BD automaticamente
    db: Session = Depends(get_db),
):
    """
    Lista atendimentos de forma paginada com múltiplos filtros.
    Contrato compatível com ZigChat GET /atendimento/listar (+ filtro
    opcional "status", que é uma extensão própria deste projeto).
    """
    try:
        # Delega a busca complexa para o Service. O Router não deve conter regras de negócio.
        resultado = AtendimentoService.listar(
            db=db, id=id, canal=canal, ativo=ativo,
            data_criacao_inicio=data_criacao_inicio, data_criacao_fim=data_criacao_fim,
            tipo=tipo, departamento_id=departamento_id, atendente_usuario_id=atendente_usuario_id,
            cliente_id=cliente_id, protocolo=protocolo, conexao_id=conexao_id, status=status,
            limit=limit, page=page, order=order,
        )

        # MELHORIA APLICADA: Em vez do "for" gigante criando dicionários, usamos o Schema.
        # O Pydantic converte automaticamente os objetos do banco para o formato de saída,
        # incluindo a formatação correta de datas e tipos opcionais.
        registros = [AtendimentoResponse.model_validate(a) for a in resultado["registros"]]

        return ZigResponse(
            codigo=0,
            dados={
                "total": resultado["total"],
                "pagina": resultado["pagina"],
                "limit": resultado["limit"],
                "paginas": resultado["paginas"],
                "registros": registros, # Retorna os dados já validados e formatados
            },
        )
    except Exception as e:
        # Em caso de falha, retorna o erro padronizado
        return ZigResponse(codigo=1, erro=str(e))


@router.get("/indicadores", response_model=ZigResponse)
def indicadores_atendimentos(
    data_criacao_inicio: Optional[str] = Query(None, example="2026-01-01"),
    data_criacao_fim: Optional[str] = Query(None, example="2026-01-30"),
    db: Session = Depends(get_db),
):
    """
    Indicadores de atendimento em tempo real, direto do banco — substitui o
    fluxo manual de extrair relatório da ZigChat, exportar em Excel e
    importar no dashboard. Endpoint próprio deste projeto (não é contrato
    ZigChat); pensado para ser consultado por polling do painel/dashboard.
    """
    try:
        return ZigResponse(codigo=0, dados=AtendimentoService.indicadores(
            db=db, data_criacao_inicio=data_criacao_inicio, data_criacao_fim=data_criacao_fim,
        ))
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
            }
        )
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


# ==============================================================================
# SEÇÃO 3: ROTAS DE ESCRITA / AÇÃO (POST)
# ==============================================================================
# Rotas responsáveis por criar, alterar ou deletar recursos no sistema.

def _buscar_instancia(db: Session, atendimento_id: int) -> Optional[str]:
    """
    Resolve o nome real da instância Evolution de um atendimento.

    NUNCA use Canal.nome como instância — Canal.nome é o nome do
    departamento/menu (ex: "Ouvidoria"), não o identificador da instância
    WhatsApp configurada na Evolution API. A instância verdadeira é
    guardada em AtendimentoContext (chave "instancia") por
    bot_service._buscar_ou_criar quando o atendimento é criado a partir do
    webhook.
    """
    ctx = AtendimentoService.buscar_context(db, atendimento_id, "instancia")
    return ctx.value if ctx and ctx.value else None


async def _avisar_paciente_transferencia(db: Session, atendimento, mensagem: Optional[str]) -> None:
    """
    Avisa o paciente por WhatsApp que seu atendimento mudou de setor/atendente.
    Nunca deixa uma falha de envio derrubar a transferência em si — só loga.
    """
    if not atendimento.telefone:
        return

    instancia = _buscar_instancia(db, atendimento.id)
    if not instancia:
        logger.warning(
            "atendimento | transferir | sem 'instancia' registrada para atendimento=%s; aviso não enviado",
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
            "Em instantes, um de nossos atendentes continuará seu atendimento por aqui."
            if setor else
            "🔄 Você foi transferido(a) para outro atendente. Em instantes, continuaremos seu atendimento."
        )

    try:
        from app.services import evolution_service
        await evolution_service.enviar_texto(
            instance=instancia, number=atendimento.telefone, text=texto,
        )
    except Exception:
        logger.exception("atendimento | transferir | falha ao avisar paciente | atendimento=%s", atendimento.id)


@router.post("/transferir", response_model=ZigResponse)
async def transferir_atendimento(body: TransferirAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Transfere o atendimento para um departamento, atendente e/ou canal, e
    avisa o paciente por WhatsApp sobre a mudança.
    Contrato compatível com ZigChat POST /atendimento/transferir.
    """
    try:
        # Validação de regra de negócio específica desta rota
        if body.departamento_id is None and body.atendente_usuario_id is None and body.canal_id is None:
            return ZigResponse(
                codigo=1,
                erro="Informe ao menos departamento_id, atendente_usuario_id ou canal_id.",
            )

        # Delega a transferência para o Service
        atendimento = AtendimentoService.transferir(
            db=db,
            atendimento_id=body.atendimento_id,
            departamento_id=body.departamento_id,
            atendente_usuario_id=body.atendente_usuario_id,
            canal_id=body.canal_id,
        )
        
        if not atendimento:
            return ZigResponse(codigo=1, erro=f"Atendimento {body.atendimento_id} não encontrado.")

        await _avisar_paciente_transferencia(db, atendimento, body.mensagem)

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
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/encerrar", response_model=ZigResponse)
async def encerrar_atendimento(body: EncerrarAtendimentoRequest, db: Session = Depends(get_db)):
    """
    Encerra um atendimento, alterando seu status para 'finalizado'.
    Se uma mensagem for informada, envia o texto via Evolution API (WhatsApp) antes de encerrar.
    É uma função 'async' porque precisa aguardar (await) a resposta da API externa.
    Contrato compatível com ZigChat POST /atendimento/encerrar.
    """
    try:
        atendimento = AtendimentoService.buscar_por_id(db, body.atendimento_id)
        if not atendimento:
            return ZigResponse(codigo=1, erro=f"Atendimento {body.atendimento_id} não encontrado.")

        # Verifica se precisa enviar mensagem antes de encerrar.
        # NOTA: usa a 'instancia' registrada em AtendimentoContext, não
        # atendimento.canal.nome — Canal.nome é o nome do departamento/menu,
        # não o identificador da instância Evolution (ver _buscar_instancia).
        if body.mensagem and atendimento.telefone:
            instancia = _buscar_instancia(db, atendimento.id)
            if instancia:
                try:
                    # Importação tardia (dentro da função) para evitar dependência circular entre módulos
                    from app.services import evolution_service
                    await evolution_service.enviar_texto(
                        instance=instancia,
                        number=atendimento.telefone,
                        text=body.mensagem,
                    )
                except Exception:
                    logger.exception(
                        "atendimento | encerrar | falha ao enviar mensagem final | atendimento=%s",
                        atendimento.id,
                    )
            else:
                logger.warning(
                    "atendimento | encerrar | sem 'instancia' registrada para atendimento=%s; mensagem não enviada",
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
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/deletarContext", response_model=ZigResponse)
def deletar_context(body: DeletarContextRequest, db: Session = Depends(get_db)):
    """
    Deleta um contexto do atendimento pela context_key.
    Contrato compatível com ZigChat POST /atendimento/deletarContext.
    """
    try:
        removido = AtendimentoService.deletar_context(
            db=db, atendimento_id=body.atendimento_id, context_key=body.context_key,
        )
        if not removido:
            return ZigResponse(codigo=1, erro="Contexto não encontrado.")
            
        return ZigResponse(codigo=0, dados={"removido": True})
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/criarAlteraContext", response_model=ZigResponse)
def criar_altera_context(body: CriarAlteraContextRequest, db: Session = Depends(get_db)):
    """
    Adiciona ou atualiza um contexto no atendimento (operação de Upsert).
    Se a context_key já existir para aquele atendimento, sobrescreve o value.
    Contrato compatível com ZigChat POST /atendimento/criarAlteraContext.
    """
    try:
        # Garante que o valor seja sempre salvo como string no banco de dados
        value_str = body.value if isinstance(body.value, str) else str(body.value)

        ctx = AtendimentoService.criar_altera_context(
            db=db, atendimento_id=body.atendimento_id, context_key=body.context_key, value=value_str,
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
