from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.security import exigir_nivel, exigir_nivel_minimo
from app.services.usuario_service import UsuarioService
from app.schemas import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListItem

router = APIRouter()

@router.get("/", response_model=List[UsuarioListItem], dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
def listar_usuarios(
    nome: Optional[str] = Query(None),
    departamentoId: Optional[int] = Query(None),
    canalId: Optional[int] = Query(None),
    nivel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    usuarios = UsuarioService.listar_usuarios(
        db=db,
        nome=nome,
        departamento_id=departamentoId,
        canal_id=canalId,
        nivel=nivel,
        status=status
    )
    return [
        UsuarioListItem(
            id=u.id,
            nome=u.nome,
            email=u.email,
            telefone=u.telefone,
            ativo=u.ativo,
            nivel_nome=u.nivel.nome if u.nivel else None,
            departamento_nome=u.departamento.nome if u.departamento else None,
            canal_nome=u.canal.nome if u.canal else None
        )
        for u in usuarios
    ]

@router.get("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = UsuarioService.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@router.post("/", response_model=UsuarioResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return UsuarioService.criar_usuario(db, usuario)

@router.put("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def atualizar_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    usuario_atualizado = UsuarioService.atualizar_usuario(db, usuario_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{usuario_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    sucesso = UsuarioService.deletar_usuario(db, usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return None
