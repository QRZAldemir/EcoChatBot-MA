from sqlalchemy.orm import Session
from app.models import Usuario, NivelUsuario
from app.schemas import UsuarioCreate, UsuarioUpdate
from app.repositories.tenant_repository import UsuarioRepository
from app.exceptions import (
    UsuarioAlreadyExists,
    UsuarioInvalidPassword,
    UsuarioNotFound,
)
from app.services.email_service import EmailService
from app.security import SECRET_KEY, JWT_ALGORITHM
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime, timedelta
import random
import string

from jose import jwt

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
# e auth.py. Os métodos de instância recebem (db, cliente_id) e usam a
# camada de repositórios (UsuarioRepository) para isolar o tenant.
# =====================================================================

    def __init__(self, db: Session, cliente_id: Optional[int] = None):
        self.db = db
        self.cliente_id = cliente_id
        self.repository = UsuarioRepository(db, cliente_id)

    # ----------------------------------------
    # UTILITÁRIOS
    # ----------------------------------------

    def _generate_temp_password(self, length: int = 10) -> str:
        """Gera senha temporária com caracteres especiais."""
        chars = string.ascii_letters + string.digits + "!@#$%&*"
        return ''.join(random.choice(chars) for _ in range(length))

    def _generate_token(self, usuario_id: int, horas: int) -> str:
        """Gera token JWT de convite/reset (mesma chave do security.py)."""
        payload = {
            "sub": str(usuario_id),
            "tipo": "convite",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=horas),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    def _link_tenant(self, path: str, token: str) -> str:
        """Monta link público do tenant."""
        dominio = f"{self.cliente_id}.ecochatmarcx.com.br" if self.cliente_id else "ecochatmarcx.com.br"
        return f"https://{dominio}{path}?token={token}"

    def _novo_usuario(self, data, senha: str, status: str) -> Usuario:
        return Usuario(
            cliente_id=self.cliente_id,
            nome=data.nome,
            email=data.email,
            telefone=getattr(data, "telefone", None),
            senha_hash=hash_senha(senha),
            nivel_id=data.nivel_id,
            departamento_id=getattr(data, "departamento_id", None),
            canal_id=getattr(data, "canal_id", None),
            ativo=status == "ativo",
            status=status,
        )

    # ----------------------------------------
    # CRUD
    # ----------------------------------------

    async def list_all(self, page: int = 1, limit: int = 50,
                       filtros: Optional[dict] = None) -> dict:
        return self.repository.list_all(page, limit, filtros)

    async def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.repository.get_by_id(usuario_id)

    def _por_email(self, email: str) -> Optional[Usuario]:
        return self.repository.get_by_email(email)

    async def create(self, data) -> Usuario:
        if self._por_email(data.email):
            raise UsuarioAlreadyExists(f"Email {data.email} já cadastrado")
        novo = self._novo_usuario(data, data.senha, "ativo")
        return self.repository.create(novo)

    async def create_admin(self, data) -> Usuario:
        if self._por_email(data.email):
            raise UsuarioAlreadyExists(f"Email {data.email} já cadastrado")
        novo = self._novo_usuario(data, data.senha, "ativo")
        novo = self.repository.create(novo)
        # Envio de boas-vindas (fallback simulado se SMTP ausente).
        EmailService.send_welcome_email(self.db, novo.email, novo.nome, data.senha)
        return novo

    async def convidar(self, data) -> dict:
        if self._por_email(data.email):
            raise UsuarioAlreadyExists(f"Email {data.email} já cadastrado")
        senha_temp = self._generate_temp_password()
        novo = self._novo_usuario(data, senha_temp, "convidado")
        novo = self.repository.create(novo)
        token = self._generate_token(novo.id, horas=24 * 7)
        link = self._link_tenant("/accept-invite", token)
        EmailService.send_invite_email(self.db, novo.email, novo.nome, senha_temp, link)
        return {
            "usuario_id": novo.id,
            "email": novo.email,
            "link_convite": link,
            "expira_em": datetime.utcnow() + timedelta(days=7),
            "mensagem": f"Convite enviado para {novo.nome}",
        }

    async def update(self, usuario_id: int, data) -> Usuario:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        update_data = data.model_dump(exclude_unset=True)
        return self.repository.update(usuario_id, update_data)

    async def update_status(self, usuario_id: int, data) -> Usuario:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        return self.repository.update(usuario_id, {
            "status": data.status,
            "ativo": data.status == "ativo",
        })

    async def delete(self, usuario_id: int) -> bool:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        return self.repository.delete(usuario_id)

    # ----------------------------------------
    # SENHA
    # ----------------------------------------

    async def change_password(self, usuario_id: int, data) -> None:
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound("Usuário não encontrado")
        if not verificar_senha(data.senha_atual, usuario.senha_hash):
            raise UsuarioInvalidPassword("Senha atual incorreta")
        self.repository.update(usuario_id, {"senha_hash": hash_senha(data.nova_senha)})

    async def reset_password(self, usuario_id: int, data) -> None:
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFound(f"Usuário {usuario_id} não encontrado")
        self.repository.update(usuario_id, {
            "senha_hash": hash_senha(data.nova_senha),
            "status": "ativo",
            "ativo": True,
        })

    async def forgot_password(self, email: str) -> dict:
        usuario = self._por_email(email)
        if not usuario:
            raise UsuarioNotFound("Email não encontrado")
        token = self._generate_token(usuario.id, horas=24)
        link = self._link_tenant("/reset-password", token)
        EmailService.send_reset_password_email(self.db, usuario.email, usuario.nome, link)
        return {"message": f"Instruções de recuperação enviadas para {email}", "email": email}

    # ----------------------------------------
    # PERMISSÕES / ESTATÍSTICAS
    # ----------------------------------------

    async def verificar_permissao(self, usuario_id: int, nivel_requerido: str) -> bool:
        """Verifica se o usuário tem o nível requerido (nome do nível)."""
        usuario = await self.get_by_id(usuario_id)
        if not usuario or not usuario.ativo:
            return False
        return (usuario.nivel.nome == nivel_requerido) if usuario.nivel else False

    async def get_atendentes_disponiveis(self) -> List[Usuario]:
        """Lista atendentes/supervisores ativos disponíveis."""
        return self.repository.list_all_flat({
            "nivel_lista": ["atendente", "supervisor"],
            "ativo": True,
        })

    async def get_estatisticas(self) -> dict:
        usuarios = self.repository.list_all_flat()
        stats = {
            "total": len(usuarios),
            "por_nivel": {},
            "por_status": {},
            "ativos": 0,
            "inativos": 0,
            "convidados": 0,
        }
        for u in usuarios:
            nivel = u.nivel.nome if u.nivel else "sem-nivel"
            stats["por_nivel"][nivel] = stats["por_nivel"].get(nivel, 0) + 1
            status = u.status or ("ativo" if u.ativo else "inativo")
            stats["por_status"][status] = stats["por_status"].get(status, 0) + 1
            if status == "ativo" or u.ativo:
                stats["ativos"] += 1
            elif status == "inativo":
                stats["inativos"] += 1
            elif status == "convidado":
                stats["convidados"] += 1
        return stats
