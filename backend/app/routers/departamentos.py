from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.departamento_service import DepartamentoService
from app.schemas import DepartamentoCreate, DepartamentoUpdate, DepartamentoResponse

router = APIRouter()

@router.get("/", response_model=List[DepartamentoResponse])
def listar_departamentos(db: Session = Depends(get_db)):
    return DepartamentoService.listar_departamentos(db)

@router.get("/{departamento_id}", response_model=DepartamentoResponse)
def buscar_departamento(departamento_id: int, db: Session = Depends(get_db)):
    departamento = DepartamentoService.buscar_por_id(db, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return departamento

@router.post("/", response_model=DepartamentoResponse, status_code=201)
def criar_departamento(departamento: DepartamentoCreate, db: Session = Depends(get_db)):
    return DepartamentoService.criar_departamento(db, departamento)

@router.put("/{departamento_id}", response_model=DepartamentoResponse)
def atualizar_departamento(departamento_id: int, departamento: DepartamentoUpdate, db: Session = Depends(get_db)):
    depto_atualizado = DepartamentoService.atualizar_departamento(db, departamento_id, departamento)
    if not depto_atualizado:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return depto_atualizado

@router.delete("/{departamento_id}", status_code=204)
def deletar_departamento(departamento_id: int, db: Session = Depends(get_db)):
    sucesso = DepartamentoService.deletar_departamento(db, departamento_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return None
