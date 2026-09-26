# ==============================================================================
# ARQUIVO.....: app/repositories/usuario_repository.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBotMarcx - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Repository do Objeto Usuario (Unit of Work)
# VERSÃO......: 3.0.0
# CRIADO EM...: 2024-01-15
# ATUALIZADO..: 2026-09-19
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: SQLAlchemy 2.0
# ==============================================================================
# DESCRIÇÃO...:
# Camada de acesso a dados especializada em Usuario. Implementa o padrão
# Unit of Work: métodos de escrita fazem apenas flush() — o commit() é
# responsabilidade do Service, garantindo atomicidade em operações
# compostas (ex.: criar usuário + vincular conexões).
#
# FUNCIONALIDADES:
# 1. Query base com filtro automático de tenant (_base)
# 2. Eager loading de relacionamentos com selectinload (evita N+1)
# 3. Busca por email dentro do tenant
# 4. Busca por login (usuario) dentro do tenant
# 5. Listagem paginada com filtros dinâmicos
# 6. Métodos add/delete que fazem flush sem commit
#
# REGRAS DE NEGÓCIO:
# - Toda query é filtrada por empresa_id (isolamento multi-tenant)
# - Nenhum método faz commit — controle transacional é do Service
#
# DEPENDÊNCIAS:
# - app.models.usuario.Usuario
# - sqlalchemy.orm.Session
#
# USADO POR:
# - app.services.usuario_service.UsuarioService
# ==============================================================================

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload
from app.models.usuario import Usuario


class UsuarioRepository:
    """Repository de Usuario com isolamento multi-tenant."""

    def __init__(self, db: Session, empresa_id: int) -> None:
        self.db = db
        self.empresa_id = empresa_id

    # --------------------------------------------------------------------------
    # QUERY BASE
    # --------------------------------------------------------------------------
    def _base(self):
        """Query base com filtro obrigatório de tenant (anti-IDOR)."""
        return self.db.query(Usuario).filter(
            Usuario.empresa_id == self.empresa_id
        )

    # --------------------------------------------------------------------------
    # LEITURA
    # --------------------------------------------------------------------------
    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """Busca usuário por ID dentro do tenant."""
        return self._base().filter(Usuario.id == usuario_id).first()

    def get_by_id_com_relacoes(self, usuario_id: int) -> Optional[Usuario]:
        """
        Busca usuário por ID com todos os relacionamentos carregados
        via selectinload (evita N+1 em serialização).
        """
        return (
            self._base()
            .filter(Usuario.id == usuario_id)
            .options(
                selectinload(Usuario.conexoes),
                selectinload(Usuario.conexao_padrao),
                selectinload(Usuario.nivel),
                selectinload(Usuario.departamento),
                selectinload(Usuario.canal),
                selectinload(Usuario.turno),
                selectinload(Usuario.empresa),
            )
            .first()
        )

    def get_by_email_in_tenant(self, email: str) -> Optional[Usuario]:
        """Busca por email dentro do tenant (validação de unicidade)."""
        return (
            self._base()
            .filter(func.lower(Usuario.email) == email.strip().lower())
            .first()
        )

    def get_by_login_in_tenant(self, usuario: str) -> Optional[Usuario]:
        """Busca por login (usuario) dentro do tenant."""
        return (
            self._base()
            .filter(func.lower(Usuario.usuario) == usuario.strip().lower())
            .first()
        )

    def listar(
        self,
        page: int = 1,
        limit: int = 20,
        filtros: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, List[Usuario]]:
        """
        Lista usuários paginados com filtros.
        Filtros aceitos:
            - nome: busca textual (nome, email, usuario)
            - departamento_id: filtro exato
            - status: 'ativo' | 'inativo' | 'pendente'
        """
        q = self._base()
        filtros = filtros or {}

        if nome := filtros.get("nome"):
            termo = f"%{nome}%"
            q = q.filter(or_(
                Usuario.nome.ilike(termo),
                Usuario.email.ilike(termo),
                Usuario.usuario.ilike(termo),
            ))

        if dep_id := filtros.get("departamento_id"):
            q = q.filter(Usuario.departamento_id == dep_id)

        if status := filtros.get("status"):
            q = q.filter(Usuario.status == status)

        total = q.count()
        items = (
            q.order_by(Usuario.nome)
            .offset((page - 1) * limit)
            .limit(limit)
            .options(
                selectinload(Usuario.conexoes),
                selectinload(Usuario.nivel),
                selectinload(Usuario.departamento),
                selectinload(Usuario.canal),
                selectinload(Usuario.turno),
            )
            .all()
        )
        return total, items

    # --------------------------------------------------------------------------
    # ESCRITA (sem commit — Unit of Work)
    # --------------------------------------------------------------------------
    def add(self, usuario: Usuario) -> Usuario:
        """Adiciona usuário à sessão e flush (sem commit)."""
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def delete(self, usuario: Usuario) -> None:
        """Remove usuário da sessão e flush (sem commit)."""
        self.db.delete(usuario)
        self.db.flush()