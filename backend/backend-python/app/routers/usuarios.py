from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.usuario_service import UsuarioService
from app.schemas import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListItem

router = APIRouter()

@router.get("/", response_model=List[UsuarioListItem])
def listar_usuarios(
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    departamentoId: Optional[int] = Query(None, description="Filtrar por departamento"),
    canalId: Optional[int] = Query(None, description="Filtrar por canal"),
    nivel: Optional[str] = Query(None, description="Filtrar por nível"),
    status: Optional[str] = Query(None, description="Filtrar por status (ativo/inativo)"),
    db: Session = Depends(get_db)
):
    """Listar usuários com filtros opcionais"""
    usuarios = UsuarioService.listar_usuarios(
        db=db,
        nome=nome,
        departamento_id=departamentoId,
        canal_id=canalId,
        nivel=nivel,
        status=status
    )
    
    # Converter para formato de lista simplificado
    resultado = []
    for usuario in usuarios:
        resultado.append(UsuarioListItem(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            telefone=usuario.telefone,
            ativo=usuario.ativo,
            nivel_nome=usuario.nivel.nome if usuario.nivel else None,
            departamento_nome=usuario.departamento.nome if usuario.departamento else None,
            canal_nome=usuario.canal.nome if usuario.canal else None
        ))
    
    return resultado

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Buscar usuário por ID"""
    usuario = UsuarioService.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@router.post("/", response_model=UsuarioResponse, status_code=201)
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Criar novo usuário"""
    # Verificar se email já existe
    existente = db.query(UsuarioService).filter_by(email=usuario.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    return UsuarioService.criar_usuario(db, usuario)

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    """Atualizar usuário existente"""
    usuario_atualizado = UsuarioService.atualizar_usuario(db, usuario_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{usuario_id}", status_code=204)
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Deletar usuário"""
    sucesso = UsuarioService.deletar_usuario(db, usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return None
