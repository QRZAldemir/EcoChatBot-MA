# ==============================================================================
# Arquivo: contatos.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Rotas da agenda de clientes WhatsApp ("Contatos" na sidebar, ver
# docs/Barra Menu.png) — base de destinatários para o disparo de Campanhas.
# ==============================================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ContatoCreate, ContatoUpdate, ContatoResponse
from app.services.contato_service import ContatoService

router = APIRouter()


@router.get("/", response_model=List[ContatoResponse])
def listar_contatos(db: Session = Depends(get_db)):
    return ContatoService.listar(db)


@router.get("/{contato_id}", response_model=ContatoResponse)
def buscar_contato(contato_id: int, db: Session = Depends(get_db)):
    contato = ContatoService.buscar_por_id(db, contato_id)
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contato


@router.post("/", response_model=ContatoResponse, status_code=201)
def criar_contato(dto: ContatoCreate, db: Session = Depends(get_db)):
    return ContatoService.criar(db, dto)


@router.put("/{contato_id}", response_model=ContatoResponse)
def atualizar_contato(contato_id: int, dto: ContatoUpdate, db: Session = Depends(get_db)):
    contato = ContatoService.atualizar(db, contato_id, dto)
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contato


@router.delete("/{contato_id}", status_code=204)
def deletar_contato(contato_id: int, db: Session = Depends(get_db)):
    sucesso = ContatoService.deletar(db, contato_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return None
