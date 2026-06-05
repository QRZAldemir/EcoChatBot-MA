from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.canal_service import CanalService
from app.schemas import CanalCreate, CanalUpdate, CanalResponse

router = APIRouter()

@router.get("/", response_model=List[CanalResponse])
def listar_canais(db: Session = Depends(get_db)):
    """Listar todos os canais"""
    return CanalService.listar_canais(db)

@router.get("/{canal_id}", response_model=CanalResponse)
def buscar_canal(canal_id: int, db: Session = Depends(get_db)):
    """Buscar canal por ID"""
    canal = CanalService.buscar_por_id(db, canal_id)
    if not canal:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return canal

@router.post("/", response_model=CanalResponse, status_code=201)
def criar_canal(canal: CanalCreate, db: Session = Depends(get_db)):
    """Criar novo canal"""
    return CanalService.criar_canal(db, canal)

@router.put("/{canal_id}", response_model=CanalResponse)
def atualizar_canal(canal_id: int, canal: CanalUpdate, db: Session = Depends(get_db)):
    """Atualizar canal existente"""
    canal_atualizado = CanalService.atualizar_canal(db, canal_id, canal)
    if not canal_atualizado:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return canal_atualizado

@router.delete("/{canal_id}", status_code=204)
def deletar_canal(canal_id: int, db: Session = Depends(get_db)):
    """Deletar canal"""
    sucesso = CanalService.deletar_canal(db, canal_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return None
