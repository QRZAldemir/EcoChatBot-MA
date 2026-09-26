from app.core.zig_response import ZigResponse
from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/enviar", response_model=ZigResponse)
async def enviar_mensagem(body: EnviarMensagemRequest):
    """
    Envia uma ou mais mensagens (texto e/ou arquivo) para um número via Evolution API.
    Contrato compatível com ZigChat POST /mensagem/enviar.
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

        except Exception as e:
            return ZigResponse(codigo=1, erro=str(e))

    return ZigResponse(codigo=0, dados={"enviados": len(resultados), "mensagens": resultados})


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


@router.post("/template", response_model=ZigResponse)
async def enviar_template(body: EnviarTemplateRequest):
    """
    Envia um template WABA para um contato via Evolution API.
    Contrato compatível com ZigChat POST /mensagem/template.
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

        return ZigResponse(codigo=0, dados=resultado)

    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


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
    """
    try:
        menu = MenuService.buscar_por_id(db, int(body.menu_id))
        if not menu:
            return ZigResponse(codigo=1, erro=f"Menu {body.menu_id} não encontrado.")

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

        return ZigResponse(codigo=0, dados=resultado)

    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


class VerificarMensagemRequest(BaseModel):
    telefone: str
    msgVerify: str          # ID da mensagem a verificar
    conexao: str            # nome da instância na Evolution API


@router.post("/verificar", response_model=ZigResponse)
async def verificar_mensagem(body: VerificarMensagemRequest):
    """
    Verifica se uma mensagem foi realmente enviada para o número informado.
    Contrato compatível com ZigChat POST /mensagem/verificar.
    """
    try:
        resultado = await evolution_service.verificar_mensagem(
            instance=body.conexao,
            number=body.telefone,
            msg_id=body.msgVerify,
        )

        mensagens = resultado.get("messages", resultado) if isinstance(resultado, dict) else resultado
        encontrada = bool(mensagens)

        return ZigResponse(
            codigo=0,
            dados={
                "encontrada": encontrada,
                "mensagem": mensagens[0] if isinstance(mensagens, list) and mensagens else mensagens,
            },
        )

    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))
