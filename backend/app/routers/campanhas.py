# ==============================================================================
# Arquivo: campanhas.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Rotas de disparo em massa de mensagens WhatsApp ("Campanhas" na sidebar,
# ver docs/Barra Menu.png).
# ==============================================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CampanhaCreate, CampanhaResponse, CampanhaDetalheResponse
from app.services.campanha_service import CampanhaService

router = APIRouter()


@router.get("/", response_model=List[CampanhaResponse])
def listar_campanhas(db: Session = Depends(get_db)):
    return CampanhaService.listar(db)


@router.get("/{campanha_id}", response_model=CampanhaDetalheResponse)
def buscar_campanha(campanha_id: int, db: Session = Depends(get_db)):
    campanha = CampanhaService.buscar_por_id(db, campanha_id)
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return campanha


@router.post("/", response_model=CampanhaResponse, status_code=201)
def criar_campanha(dto: CampanhaCreate, db: Session = Depends(get_db)):
    """'+ Nova campanha' — cria em rascunho, vinculada aos contatos selecionados."""
    return CampanhaService.criar(db, dto)


@router.delete("/{campanha_id}", status_code=204)
def deletar_campanha(campanha_id: int, db: Session = Depends(get_db)):
    sucesso = CampanhaService.deletar(db, campanha_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return None


@router.post("/{campanha_id}/disparar", response_model=CampanhaResponse)
async def disparar_campanha(campanha_id: int, db: Session = Depends(get_db)):
    """Botão 'Disparar' — envia a mensagem para todos os contatos pendentes."""
    campanha = await CampanhaService.disparar(db, campanha_id)
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return campanha
