from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.security import exigir_nivel, exigir_nivel_minimo
from app.services.modelo_mensagem_service import ModeloMensagemService
from app.schemas import ModeloMensagemCreate, ModeloMensagemUpdate, ModeloMensagemResponse

router = APIRouter()


@router.get("/", response_model=List[ModeloMensagemResponse])
def listar_modelos(
    departamento_id: Optional[int] = Query(None),
    apenas_ativos: bool = Query(False),
    db: Session = Depends(get_db),
):
    return ModeloMensagemService.listar(db, departamento_id=departamento_id, apenas_ativos=apenas_ativos)


@router.get("/{modelo_id}", response_model=ModeloMensagemResponse)
def buscar_modelo(modelo_id: int, db: Session = Depends(get_db)):
    modelo = ModeloMensagemService.buscar_por_id(db, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo de mensagem não encontrado")
    return modelo


@router.post("/", response_model=ModeloMensagemResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def criar_modelo(modelo: ModeloMensagemCreate, db: Session = Depends(get_db)):
    return ModeloMensagemService.criar(db, modelo)


@router.put("/{modelo_id}", response_model=ModeloMensagemResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def atualizar_modelo(modelo_id: int, modelo: ModeloMensagemUpdate, db: Session = Depends(get_db)):
    atualizado = ModeloMensagemService.atualizar(db, modelo_id, modelo)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Modelo de mensagem não encontrado")
    return atualizado


@router.delete("/{modelo_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
def deletar_modelo(modelo_id: int, db: Session = Depends(get_db)):
    if not ModeloMensagemService.deletar(db, modelo_id):
        raise HTTPException(status_code=404, detail="Modelo de mensagem não encontrado")
