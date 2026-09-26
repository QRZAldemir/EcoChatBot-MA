"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: routers/conexoes.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Gerenciar o ciclo de vida das instâncias WhatsApp/WABA via Evolution API.
Substitui o código legado duplicado, oferecendo endpoints completos para 
criação, QR Code, status, reconexão, logout e definições de instância.

ARQUITETURA E INTEGRAÇÃO:
Camada de Apresentação (API). Consome o `EvolutionApiClient` (Service).
Integração direta com o Frontend (Angular `conexoes.component.ts`).
================================================================================
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_current_user, get_db
from app.services.evolution_api_client import EvolutionApiClient
from app.schemas.conexao import ConexaoCreate, ConexaoUpdate

router = APIRouter(prefix="/api/conexoes", tags=["Conexões WhatsApp/WABA"])

@router.get("/", status_code=status.HTTP_200_OK)
async def listar_instancias(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    return await client.list_instances()

@router.get("/{instancia_id}", status_code=status.HTTP_200_OK)
async def obter_instancia(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    return await client.get_instance(instancia_id)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_instancia(data: ConexaoCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    return await client.create_instance(data.dict())

@router.put("/{instancia_id}", status_code=status.HTTP_200_OK)
async def atualizar_instancia(instancia_id: str, data: ConexaoUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    return await client.update_instance(instancia_id, data.dict(exclude_unset=True))

@router.delete("/{instancia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_instancia(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.delete_instance(instancia_id)

@router.post("/{instancia_id}/status", status_code=status.HTTP_200_OK)
async def obter_status(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    return await client.get_connection_state(instancia_id)

@router.post("/{instancia_id}/desconectar", status_code=status.HTTP_200_OK)
async def desconectar(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.logout(instancia_id)
    return {"message": "Instância desconectada."}

@router.post("/{instancia_id}/reconectar", status_code=status.HTTP_200_OK)
async def reconectar(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.reconnect(instancia_id)
    return {"message": "Reconexão solicitada."}

@router.post("/{instancia_id}/limpar-fila", status_code=status.HTTP_200_OK)
async def limpar_fila(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.clear_queue(instancia_id)
    return {"message": "Fila de mensagens limpa."}

@router.post("/{instancia_id}/tornar-padrao", status_code=status.HTTP_200_OK)
async def tornar_padrao(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.set_default(instancia_id)
    return {"message": "Instância definida como padrão."}

@router.post("/{instancia_id}/alternar-ativo", status_code=status.HTTP_200_OK)
async def alternar_ativo(instancia_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    client = EvolutionApiClient(db, user.cliente_id)
    await client.toggle_active(instancia_id)
    return {"message": "Status ativo/inativo alternado."}