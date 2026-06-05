from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.deepseek_service import DeepSeekService

router = APIRouter()
deepseek_service = DeepSeekService()

class MensagemIA(BaseModel):
    role: str  # 'user', 'assistant', ou 'system'
    content: str

class ConversaRequest(BaseModel):
    mensagens: List[MensagemIA]
    canal: str

class OpcaoRequest(BaseModel):
    opcao: str
    canal: str
    contexto: Optional[str] = ""

class RespostaIA(BaseModel):
    resposta: str
    tokens: Optional[int] = 0

@router.post("/conversar", response_model=RespostaIA)
async def conversar_ia(request: ConversaRequest):
    """
    Enviar conversa para IA e obter resposta
    
    - **mensagens**: Histórico da conversa
    - **canal**: Canal de atendimento atual
    """
    # Converter mensagens para formato esperado pelo serviço
    mensagens_dict = [{"role": m.role, "content": m.content} for m in request.mensagens]
    
    resultado = await deepseek_service.conversar(mensagens_dict, request.canal)
    
    return RespostaIA(
        resposta=resultado["resposta"],
        tokens=resultado.get("tokens", 0)
    )

@router.post("/opcao", response_model=RespostaIA)
async def responder_opcao(request: OpcaoRequest):
    """
    Gerar resposta para opção selecionada pelo usuário
    
    - **opcao**: Opção escolhida pelo paciente
    - **canal**: Canal de atendimento
    - **contexto**: Contexto adicional (opcional)
    """
    resultado = await deepseek_service.responder_opcao(
        request.opcao, 
        request.canal, 
        request.contexto
    )
    
    return RespostaIA(
        resposta=resultado["resposta"],
        tokens=resultado.get("tokens", 0)
    )
