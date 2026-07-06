from sqlalchemy.orm import Session
from app.models import Usuario, NivelUsuario
from app.schemas import UsuarioCreate, UsuarioUpdate
from passlib.context import CryptContext
from typing import List, Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

class UsuarioService:

    @staticmethod
    def listar_usuarios(
        db: Session,
        nome: Optional[str] = None,
        departamento_id: Optional[int] = None,
        canal_id: Optional[int] = None,
        nivel: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Usuario]:
        query = db.query(Usuario)
        if nome:
            query = query.filter(Usuario.nome.ilike(f"%{nome}%"))
        if departamento_id:
            query = query.filter(Usuario.departamento_id == departamento_id)
        if canal_id:
            query = query.filter(Usuario.canal_id == canal_id)
        if nivel:
            query = query.join(NivelUsuario).filter(NivelUsuario.nome == nivel)
        if status:
            query = query.filter(Usuario.ativo == (status.lower() == 'ativo'))
        return query.all()

    @staticmethod
    def buscar_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()

    @staticmethod
    def buscar_por_email(db: Session, email: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def criar_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
        db_usuario = Usuario(
            nome=usuario.nome,
            email=usuario.email,
            senha_hash=hash_senha(usuario.senha),
            telefone=usuario.telefone,
            nivel_id=usuario.nivel_id,
            departamento_id=usuario.departamento_id,
            canal_id=usuario.canal_id,
            ativo=usuario.ativo
        )
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario

    @staticmethod
    def atualizar_usuario(db: Session, usuario_id: int, usuario: UsuarioUpdate) -> Optional[Usuario]:
        db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not db_usuario:
            return None
        update_data = usuario.model_dump(exclude_unset=True)
        if 'senha' in update_data and update_data['senha']:
            update_data['senha_hash'] = hash_senha(update_data.pop('senha'))
        for campo, valor in update_data.items():
            setattr(db_usuario, campo, valor)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario

    @staticmethod
    def deletar_usuario(db: Session, usuario_id: int) -> bool:
        db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not db_usuario:
            return False
        db.delete(db_usuario)
        db.commit()
        return True

    @staticmethod
    def agrupar_por_departamento(db: Session) -> dict:
        usuarios = db.query(Usuario).all()
        resultado = {}
        for usuario in usuarios:
            depto_nome = usuario.departamento.nome if usuario.departamento else "Sem Departamento"
            resultado.setdefault(depto_nome, []).append(usuario)
        return resultado
