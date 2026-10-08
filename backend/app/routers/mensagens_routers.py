<<<<<<< Updated upstream
from app.core.zig_response import ZigResponse
from fastapi import APIRouter, Depends, HTTPException
=======
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · mensagens_routers
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     mensagens_routers.py
@module   Backend / App / Routers / mensagens_routers
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Saída de mensagem para o canal do cliente: texto, template aprovado e
menu interativo. É o caminho que o painel usa para falar com quem está do
outro lado.

Este é o ÚNICO grupo de rotas do projeto que fala com a Evolution API
diretamente, sem passar por `CanalService`. A diferença é intencional:
aqui não há canais para gerenciar, só uma mensagem para despachar.

O QUE ESTE ARQUIVO É
───────────────────
A borda de saída. Recebe o que enviar, resolve o destino e chama
`evolution_service`. Não guarda nada no banco — o histórico de mensagem é
de `canais`/`atendimentos`, e duplicar isso aqui criaria duas verdades.

O OBJETO
────────
O objeto principal é o `router` (`APIRouter`), montado por `main.py` em
`/api/mensagem`. Os objetos de entrada são os modelos Pydantic deste
próprio arquivo — `EnviarMensagemRequest`, `EnviarTemplateRequest`,
`MenuEnviarRequest`, `VerificarMensagemRequest` — mais `MensagemItem`,
que representa uma mensagem já existente dentro de um payload de menu.

    Modelos Pydantic e não dicts porque o alerta de erro do FastAPI sai
    com o nome do campo e o tipo esperado. Com dict, o atendente recebe
    um 422 que só diz "invalid body".

ENDPOINTS
─────────
    POST /api/mensagem/enviar       texto simples
    POST /api/mensagem/template     template aprovado pelo Meta
    POST /api/mensagem/menuEnviar   menu interativo (lista de opções)
    POST /api/mensagem/verificar    confirma entrega/leitura

ERRO EXTERNO VIRA 502, NÃO 500
──────────────────────────────
A Evolution é um serviço de terceiro. Quando ela responde 404 (número
inexistente) ou 500, este arquivo traduz para `HTTPException(502)`.

O motivo é a distinção que o cliente precisa fazer: 502 é "a Evolution
está com problema, tente de novo", 500 é "o servidor do EcoChat está com
problema, chame o suporte". Sem essa tradução, uma falha do WhatsApp
aparecia como bug do EcoChat e abria chamado de suporte falso.

Uma consequência prática: os `except HTTPException: raise` espalhados
pelo arquivo existem para o `raise` translating NÃO ser engolido por um
`except Exception` genérico e reembalhado como 500.

CONTRATO DE RESPOSTA
────────────────────
Sucesso: `SuccessResponse` (`app/schemas/response_schemas.py`).
Erro: `ErrorResponse`. Nunca 200 com corpo de erro.

RELACIONAMENTO
──────────────
    ┌──────────────────────────────────────────────────────────────────┐
    │ main.py  monta em /api/mensagem                                 │
    │   └─► mensagens_routers      você está aqui                      │
    │         ├─► evolution_service   HTTP para a Evolution           │
    │         └─► MenuService        (só em /menuEnviar)              │
    └──────────────────────────────────────────────────────────────────┘
"""

from app.schemas.response_schemas import SuccessResponse
from fastapi import APIRouter, Depends, HTTPException, status
>>>>>>> Stashed changes
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import evolution_service
from app.services.menu_service import MenuService

router = APIRouter()


class MensagemItem(BaseModel):
    mensagem: Optional[str] = None
    arquivo: Optional[str] = None  # URL pública do arquivo


class EnviarMensagemRequest(BaseModel):
    mensagens: List[MensagemItem]
    telefone: str
    lid: Optional[str] = None
    cliente_id: Optional[int] = None
    conexao: str                       # nome da instância na Evolution API
    nome: Optional[str] = None
    transferir: bool = False
    interna: bool = False
    verifica_numero: bool = True
    finalizarAtendimento: bool = False


<<<<<<< Updated upstream
@router.post("/enviar", response_model=ZigResponse)
async def enviar_mensagem(body: EnviarMensagemRequest):
    """
    Envia uma ou mais mensagens (texto e/ou arquivo) para um número via Evolution API.
    Contrato compatível com ZigChat POST /mensagem/enviar.
=======
@router.post("/enviar", response_model=SuccessResponse)
async def enviar_mensagem(body: EnviarMensagemRequest):
    """
    Envia uma ou mais mensagens (texto e/ou arquivo) para um número via Evolution API.
    Envia via Evolution API e devolve o envelope nativo
    `{mensagem, dados}`. Falha da API externa responde 502.
>>>>>>> Stashed changes
    """
    resultados = []

    for item in body.mensagens:
        try:
            if item.arquivo:
                mediatype = evolution_service._detectar_mediatype(item.arquivo)
                resultado = await evolution_service.enviar_midia(
                    instance=body.conexao,
                    number=body.telefone,
                    media_url=item.arquivo,
                    caption=item.mensagem,
                    mediatype=mediatype,
                )
            elif item.mensagem:
                resultado = await evolution_service.enviar_texto(
                    instance=body.conexao,
                    number=body.telefone,
                    text=item.mensagem,
                )
            else:
                continue

            resultados.append(resultado)

<<<<<<< Updated upstream
        except Exception as e:
            return ZigResponse(codigo=1, erro=str(e))

    return ZigResponse(codigo=0, dados={"enviados": len(resultados), "mensagens": resultados})
=======
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na Evolution API: {e}",
        )

    return SuccessResponse(
        mensagem=f"{len(resultados)} mensagem(ns) enviada(s) com sucesso",
        dados={"enviados": len(resultados), "mensagens": resultados},
    )
>>>>>>> Stashed changes


class TemplateParametro(BaseModel):
    type: str                          # "text", "image", "document", etc.
    text: Optional[str] = None
    parameter_name: Optional[str] = None


class EnviarTemplateRequest(BaseModel):
    contato_nome: str
    contato_telefone: str
    conexao_nome: str                  # nome da instância na Evolution API
    template_id: str                   # nome do template WABA
    menu_id: Optional[int] = None
    language: str = "pt_BR"
    header_parameters: List[TemplateParametro] = []
    body_parameters: List[TemplateParametro] = []


@router.post("/template", response_model=SuccessResponse)
async def enviar_template(body: EnviarTemplateRequest):
    """
    Envia um template WABA para um contato via Evolution API.
<<<<<<< Updated upstream
    Contrato compatível com ZigChat POST /mensagem/template.
=======
    Envia um template aprovado via Evolution API. Resposta nativa;
    falha da API externa responde 502.
>>>>>>> Stashed changes
    """
    try:
        def _serializar(params: List[TemplateParametro]) -> list:
            result = []
            for p in params:
                item: dict = {"type": p.type}
                if p.text is not None:
                    item["text"] = p.text
                if p.parameter_name is not None:
                    item["parameter_name"] = p.parameter_name
                result.append(item)
            return result

        resultado = await evolution_service.enviar_template(
            instance=body.conexao_nome,
            number=body.contato_telefone,
            template_name=body.template_id,
            language=body.language,
            header_parameters=_serializar(body.header_parameters),
            body_parameters=_serializar(body.body_parameters),
        )

<<<<<<< Updated upstream
        return ZigResponse(codigo=0, dados=resultado)

=======
        return SuccessResponse(mensagem="Mensagem enviada com sucesso", dados=resultado)

    except HTTPException:
        raise
>>>>>>> Stashed changes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na Evolution API: {e}",
        )


class MenuEnviarRequest(BaseModel):
    mensagens: List[MensagemItem]
    telefone: str
    lid: Optional[str] = None
    cliente_id: Optional[int] = None
    conexao: str
    nome: Optional[str] = None
    menu_id: str


<<<<<<< Updated upstream
class MenuEnviarRequest(BaseModel):
    mensagens: List[MensagemItem]
    telefone: str
    lid: Optional[str] = None
    cliente_id: Optional[int] = None
    conexao: str
    nome: Optional[str] = None
    menu_id: str


@router.post("/menuEnviar", response_model=ZigResponse)
async def menu_enviar(body: MenuEnviarRequest, db: Session = Depends(get_db)):
    """
    Envia um menu interativo (lista) para um cliente via Evolution API.
    Contrato compatível com ZigChat POST /mensagem/menuEnviar.
=======
@router.post("/menuEnviar", response_model=SuccessResponse)
async def menu_enviar(body: MenuEnviarRequest, db: Session = Depends(get_db)):
    """
    Envia um menu interativo (lista) para um cliente via Evolution API.
    Envia um menu interativo. Menu inexistente responde 404;
    falha da API externa responde 502.
>>>>>>> Stashed changes
    """
    try:
        menu = MenuService.buscar_por_id(db, int(body.menu_id))
        if not menu:
<<<<<<< Updated upstream
            return ZigResponse(codigo=1, erro=f"Menu {body.menu_id} não encontrado.")
=======
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu {body.menu_id} não encontrado.",
            )
>>>>>>> Stashed changes

        sections = [
            {
                "title": menu.titulo,
                "rows": [
                    {
                        "title": opcao.titulo,
                        "description": opcao.descricao or "",
                        "rowId": opcao.row_id,
                    }
                    for opcao in menu.opcoes
                ],
            }
        ]

        texto = body.mensagens[0].mensagem if body.mensagens else menu.descricao or menu.titulo

        resultado = await evolution_service.enviar_lista(
            instance=body.conexao,
            number=body.telefone,
            title=menu.titulo,
            description=texto,
            button_text=menu.texto_botao or "Ver opções",
            sections=sections,
            footer=menu.rodape,
        )

<<<<<<< Updated upstream
        return ZigResponse(codigo=0, dados=resultado)

=======
        return SuccessResponse(mensagem="Mensagem enviada com sucesso", dados=resultado)

    except HTTPException:
        raise
>>>>>>> Stashed changes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na Evolution API: {e}",
        )


class VerificarMensagemRequest(BaseModel):
    telefone: str
    msgVerify: str          # ID da mensagem a verificar
    conexao: str            # nome da instância na Evolution API


<<<<<<< Updated upstream
class VerificarMensagemRequest(BaseModel):
    telefone: str
    msgVerify: str          # ID da mensagem a verificar
    conexao: str            # nome da instância na Evolution API


@router.post("/verificar", response_model=ZigResponse)
async def verificar_mensagem(body: VerificarMensagemRequest):
    """
    Verifica se uma mensagem foi realmente enviada para o número informado.
    Contrato compatível com ZigChat POST /mensagem/verificar.
=======
@router.post("/verificar", response_model=SuccessResponse)
async def verificar_mensagem(body: VerificarMensagemRequest):
    """
    Verifica se uma mensagem foi realmente enviada para o número informado.
    Confere se a mensagem chegou ao número. O campo `encontrada`
    dentro de `dados` é o que a tela lê.
>>>>>>> Stashed changes
    """
    try:
        resultado = await evolution_service.verificar_mensagem(
            instance=body.conexao,
            number=body.telefone,
            msg_id=body.msgVerify,
        )

        mensagens = resultado.get("messages", resultado) if isinstance(resultado, dict) else resultado
        encontrada = bool(mensagens)

        return SuccessResponse(
            mensagem="Mensagem verificada com sucesso",
            dados={
                "encontrada": encontrada,
                "mensagem": mensagens[0] if isinstance(mensagens, list) and mensagens else mensagens,
            },
        )

<<<<<<< Updated upstream
=======
    except HTTPException:
        raise
>>>>>>> Stashed changes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na Evolution API: {e}",
        )
