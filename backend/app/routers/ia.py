from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.deepseek_service import DeepSeekService

router = APIRouter()
deepseek_service = DeepSeekService()

class MensagemIA(BaseModel):
    role: str
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
    mensagens_dict = [{"role": m.role, "content": m.content} for m in request.mensagens]
    resultado = await deepseek_service.conversar(mensagens_dict, request.canal)
    return RespostaIA(resposta=resultado["resposta"], tokens=resultado.get("tokens", 0))

@router.post("/opcao", response_model=RespostaIA)
async def responder_opcao(request: OpcaoRequest):
    resultado = await deepseek_service.responder_opcao(request.opcao, request.canal, request.contexto)
    return RespostaIA(resposta=resultado["resposta"], tokens=resultado.get("tokens", 0))
