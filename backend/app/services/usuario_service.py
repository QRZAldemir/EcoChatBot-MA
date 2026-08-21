from sqlalchemy.orm import Session
from app.models import Usuario, NivelUsuario
from app.schemas import UsuarioCreate, UsuarioUpdate
from app.exceptions import (
    UsuarioAlreadyExists,
    UsuarioInvalidPassword,
    UsuarioNotFound,
)
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


# =====================================================================
# MÉTODOS DE INSTÂNCIA (multi-tenant) — usados pelo router /tenant/usuarios
# =====================================================================
# Mantêm os métodos estáticos acima para compatibilidade com /api/usuarios
# e auth.py. Os métodos de instância recebem (db, cliente_id) e usam
# usuario.cliente_id para isolar o tenant.
# =====================================================================

    def __init__(self, db: Session, cliente_id: Optional[int] = None):
        self.db = db
        self.cliente_id = cliente_id

    def _base(self):
        query = self.db.query(Usuario)
        if self.cliente_id is not None:
            query = query.filter(Usuario.cliente_id == self.cliente_id)
        return query

    async def list_all(self, page: int = 1, limit: int = 50,
                       filtros: Optional[dict] = None) -> dict:
        filtros = filtros or {}
        query = self._base()

        if filtros.get('nivel'):
            query = query.join(NivelUsuario).filter(NivelUsuario.nome == filtros['nivel'])
        if filtros.get('status'):
            query = query.filter(Usuario.status == filtros['status'])
        if filtros.get('search'):
            termo = f"%{filtros['search']}%"
            query = query.filter(
                Usuario.nome.ilike(termo) | Usuario.email.ilike(termo)
            )

        total = query.count()
        registros = query.order_by(Usuario.nome.asc()).offset((page - 1) * limit).limit(limit).all()
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": registros,
        }

    async def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        return self._base().filter(Usuario.id == usuario_id).first()

    def _por_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    async def create(self, data) -> Usuario:
        if self._por_email(data.email):
            raise UsuarioAlreadyExists(f"Email {data.email} já cadastrado")
        novo = Usuario(
            cliente_id=self.cliente_id,
            nome=data.nome,
            email=data.email,
            telefone=data.telefone,
            senha_hash=hash_senha(data.senha),
            nivel_id=data.nivel_id,
            departamento_id=data.departamento_id,
            canal_id=data.canal_id,
            ativo=data.ativo,
            status="ativo",
        )
        self.db.add(novo)
        self.db.commit()
        self.db.refresh(novo)
        return novo

    async def create_admin(self, data) -> Usuario:
        return await self.create(data)

    async def convidar(self, data) -> dict:
        novo = await self.create(data)
        return {
            "usuario_id": novo.id,
            "email": novo.email,
            "mensagem": f"Usuário {novo.nome} criado com sucesso.",
        }

    async def update(self, usuario_id: int, data) -> Usuario:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        update_data = data.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    async def update_status(self, usuario_id: int, data) -> Usuario:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        usuario.status = data.status
        usuario.ativo = data.status == "ativo"
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    async def delete(self, usuario_id: int) -> bool:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        usuario.ativo = False
        usuario.status = "inativo"
        self.db.commit()
        return True

    async def change_password(self, usuario_id: int, data) -> None:
        usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise UsuarioNotFound("Usuário não encontrado")
        if not verificar_senha(data.senha_atual, usuario.senha_hash):
            raise UsuarioInvalidPassword("Senha atual incorreta")
        usuario.senha_hash = hash_senha(data.nova_senha)
        self.db.commit()

    async def reset_password(self, usuario_id: int, data) -> None:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        usuario.senha_hash = hash_senha(data.nova_senha)
        self.db.commit()

    async def forgot_password(self, email: str) -> dict:
        usuario = self._por_email(email)
        if not usuario:
            raise UsuarioNotFound("Email não encontrado")
        # Em produção, gerar token e enviar email. Aqui retornamos instrução.
        return {"message": f"Instruções de recuperação enviadas para {email}"}

    async def get_estatisticas(self) -> dict:
        query = self._base()
        total = query.count()
        ativos = query.filter(Usuario.ativo == True).count()
        return {
            "total": total,
            "ativos": ativos,
            "inativos": total - ativos,
        }
