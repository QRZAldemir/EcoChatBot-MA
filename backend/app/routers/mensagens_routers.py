"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Roteamento de Mensagens
───────────────────────────────────────────────────────────────────────────
@file     mensagens_routers.py
@module   Routers / Mensagens
@desc     Endpoints para envio e verificação de mensagens via Evolution API
          Responsabilidades:
            1. Envio de mensagens de texto
            2. Envio de mídias (imagens, documentos, áudios)
            3. Envio de templates WABA
            4. Envio de menus interativos
            5. Verificação de status de mensagens
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: padronização de interfaces, tratamento de erros
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.zig_response import ZigResponse
from app.services import evolution_service
from app.services.menu_service import MenuService

router = APIRouter()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. MODELOS DE DADOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MensagemItem(BaseModel):
    """Item de mensagem (texto ou mídia)"""
    mensagem: Optional[str] = Field(None, description="Conteúdo da mensagem de texto")
    arquivo: Optional[str] = Field(None, description="URL pública do arquivo")
    media_type: Optional[str] = Field(None, description="Tipo do arquivo (image, audio, document)")


class EnviarMensagemRequest(BaseModel):
    """Request para envio de mensagens"""
    mensagens: List[MensagemItem]
    telefone: str = Field(..., description="Número de telefone destinatário")
    conexao: str = Field(..., description="Nome da instância na Evolution API")
    lid: Optional[str] = Field(None, description="ID local da conversa")
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    nome: Optional[str] = Field(None, description="Nome do remetente")
    transferir: bool = Field(False, description="Transferir atendimento")
    interna: bool = Field(False, description="Mensagem interna")
    verifica_numero: bool = Field(True, description="Validar número")
    finalizar_atendimento: bool = Field(False, description="Finalizar atendimento")


class TemplateParametro(BaseModel):
    """Parâmetro do template WABA"""
    type: str = Field(..., description="Tipo do parâmetro (text, image, document)")
    text: Optional[str] = Field(None, description="Conteúdo do parâmetro")
    parameter_name: Optional[str] = Field(None, description="Nome do parâmetro")


class EnviarTemplateRequest(BaseModel):
    """Request para envio de template WABA"""
    contato_nome: str = Field(..., description="Nome do contato")
    contato_telefone: str = Field(..., description="Telefone do contato")
    conexao_nome: str = Field(..., description="Nome da instância")
    template_id: str = Field(..., description="ID do template")
    language: str = Field("pt_BR", description="Idioma do template")
    header_parameters: List[TemplateParametro] = Field(default_factory=list)
    body_parameters: List[TemplateParametro] = Field(default_factory=list)


class MenuEnviarRequest(BaseModel):
    """Request para envio de menu interativo"""
    mensagens: List[MensagemItem]
    telefone: str = Field(..., description="Número de telefone")
    conexao: str = Field(..., description="Nome da instância")
    menu_id: str = Field(..., description="ID do menu")
    lid: Optional[str] = Field(None, description="ID local da conversa")
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    nome: Optional[str] = Field(None, description="Nome do remetente")


class VerificarMensagemRequest(BaseModel):
    """Request para verificação de mensagem"""
    telefone: str = Field(..., description="Número de telefone")
    msg_verify: str = Field(..., description="ID da mensagem a verificar")
    conexao: str = Field(..., description="Nome da instância")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. FUNÇÕES AUXILIARES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _serializar_template_params(params: List[TemplateParametro]) -> List[Dict[str, Any]]:
    """Serializa parâmetros do template para formato da Evolution API"""
    return [
        {
            "type": p.type,
            **({"text": p.text} if p.text is not None else {}),
            **({"parameter_name": p.parameter_name} if p.parameter_name is not None else {})
        }
        for p in params
    ]


async def _enviar_mensagem_item(item: MensagemItem, conexao: str, telefone: str) -> Dict[str, Any]:
    """Envia um item de mensagem (texto ou mídia)"""
    if item.arquivo:
        if not item.media_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de mídia é obrigatório quando envia arquivo"
            )
        return await evolution_service.enviar_midia(
            instance=conexao,
            number=telefone,
            media_url=item.arquivo,
            caption=item.mensagem,
            mediatype=item.media_type,
        )
    elif item.mensagem:
        return await evolution_service.enviar_texto(
            instance=conexao,
            number=telefone,
            text=item.mensagem,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário informar mensagem ou arquivo"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/enviar", response_model=ZigResponse)
async def enviar_mensagem(body: EnviarMensagemRequest):
    """Envia uma ou mais mensagens (texto e/ou arquivo)"""
    resultados = []
    
    try:
        for item in body.mensagens:
            resultado = await _enviar_mensagem_item(item, body.conexao, body.telefone)
            resultados.append(resultado)
            
        return ZigResponse(
            codigo=0,
            dados={"enviados": len(resultados), "mensagens": resultados}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/template", response_model=ZigResponse)
async def enviar_template(body: EnviarTemplateRequest):
    """Envia template WABA"""
    try:
        resultado = await evolution_service.enviar_template(
            instance=body.conexao_nome,
            number=body.contato_telefone,
            template_name=body.template_id,
            language=body.language,
            header_parameters=_serializar_template_params(body.header_parameters),
            body_parameters=_serializar_template_params(body.body_parameters),
        )
        
        return ZigResponse(codigo=0, dados=resultado)
        
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/menuEnviar", response_model=ZigResponse)
async def menu_enviar(body: MenuEnviarRequest, db: Session = Depends(get_db)):
    """Envia menu interativo"""
    try:
        menu = MenuService.buscar_por_id(db, int(body.menu_id))
        if not menu:
            return ZigResponse(codigo=1, erro=f"Menu {body.menu_id} não encontrado")

        sections = [{
            "title": menu.titulo,
            "rows": [
                {
                    "title": opcao.titulo,
                    "description": opcao.descricao or "",
                    "rowId": opcao.row_id,
                }
                for opcao in menu.opcoes
            ],
        }]

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
        
    except HTTPException:
        raise
    except Exception as e:
        return ZigResponse(codigo=1, erro=str(e))


@router.post("/verificar", response_model=ZigResponse)
async def verificar_mensagem(body: VerificarMensagemRequest):
    """Verifica status da mensagem"""
    try:
        resultado = await evolution_service.verificar_mensagem(
            instance=body.conexao,
            number=body.telefone,
            msg_id=body.msg_verify,
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
