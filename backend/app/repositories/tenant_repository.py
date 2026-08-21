"""
Repositório de Usuários — isolamento multi-tenant.

Camada de acesso a dados centralizada. Cada método aplica o filtro de
``cliente_id`` (tenant), garantindo que um usuário só enxerga/opera sobre
registros do seu próprio cliente.

Adaptado ao modelo real em app/models/__init__.py:
    Usuario: id, cliente_id, nome, email, senha_hash, telefone, nivel_id,
             departamento_id, canal_id, ativo (bool), status (string),
             criado_em, atualizado_em.
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import NivelUsuario, Usuario


class UsuarioRepository:
    """Acesso a dados de Usuario com isolamento por cliente (tenant)."""

    def __init__(self, db: Session, cliente_id: Optional[int] = None):
        self.db = db
        self.cliente_id = cliente_id

    def _base(self):
        """Query base já filtrada pelo tenant (cliente_id), quando definido."""
        query = self.db.query(Usuario)
        if self.cliente_id is not None:
            query = query.filter(Usuario.cliente_id == self.cliente_id)
        return query

    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtém um usuário do tenant por ID."""
        return self._base().filter(Usuario.id == usuario_id).first()

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário por email (sem filtro de tenant — email é global/único)."""
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def get_by_email_in_tenant(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário do tenant por email."""
        return self._base().filter(Usuario.email == email).first()

    def list_all(
        self,
        page: int = 1,
        limit: int = 50,
        filtros: Optional[Dict] = None,
    ) -> Dict:
        """Lista usuários do tenant com paginação e filtros."""
        filtros = filtros or {}
        query = self._base()

        if filtros.get("nivel"):
            query = query.join(NivelUsuario).filter(
                NivelUsuario.nome == filtros["nivel"]
            )
        if filtros.get("nivel_lista"):
            # Lista de níveis (ex.: atendentes/supervisores disponíveis)
            query = query.join(NivelUsuario).filter(
                NivelUsuario.nome.in_(filtros["nivel_lista"])
            )
        if filtros.get("status"):
            query = query.filter(Usuario.status == filtros["status"])
        if filtros.get("ativo") is not None:
            query = query.filter(Usuario.ativo == filtros["ativo"])
        if filtros.get("search"):
            termo = f"%{filtros['search']}%"
            query = query.filter(
                Usuario.nome.ilike(termo) | Usuario.email.ilike(termo)
            )

        total = query.count()
        registros = (
            query.order_by(Usuario.nome.asc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return {"total": total, "page": page, "limit": limit, "data": registros}

    def list_all_flat(self, filtros: Optional[Dict] = None) -> List[Usuario]:
        """Retorna todos os registros (sem paginação), útil para estatísticas."""
        filtros = filtros or {}
        query = self._base()

        if filtros.get("nivel_lista"):
            query = query.join(NivelUsuario).filter(
                NivelUsuario.nome.in_(filtros["nivel_lista"])
            )
        if filtros.get("status"):
            query = query.filter(Usuario.status == filtros["status"])
        if filtros.get("ativo") is not None:
            query = query.filter(Usuario.ativo == filtros["ativo"])

        return query.all()

    def create(self, usuario: Usuario) -> Usuario:
        """Persiste um novo usuário."""
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def update(self, usuario_id: int, dados: Dict) -> Optional[Usuario]:
        """Atualiza campos do usuário do tenant."""
        usuario = self.get_by_id(usuario_id)
        if not usuario:
            return None
        for campo, valor in dados.items():
            if hasattr(usuario, campo):
                setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def delete(self, usuario_id: int) -> bool:
        """Soft delete: desativa o usuário do tenant."""
        usuario = self.get_by_id(usuario_id)
        if not usuario:
            return False
        usuario.ativo = False
        usuario.status = "inativo"
        self.db.commit()
        return True

    def count(self) -> int:
        """Total de usuários do tenant."""
        return self._base().count()
