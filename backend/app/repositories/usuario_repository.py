"""
================================================================================
PROJETO: EcoChatBotMarcx - Omnichannel SaaS
MÓDULO: usuario_repository.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Centralizar o acesso a dados da entidade `Usuario`, aplicando rigorosamente 
o isolamento multi-tenant (filtro por `cliente_id`). Contém a lógica de 
negócio complexa para paginação, filtros avançados (nível, status, busca textual) 
e soft-delete, adaptada para o paradigma assíncrono do SQLAlchemy 2.0.

ARQUITETURA E INTEGRAÇÃO:
Esta classe herda de `BaseRepository[Usuario]`. 
CONEXÃO: Ela é injetada e utilizada exclusivamente pelo `UsuarioService` (Camada de Serviço). 
O `UsuarioService` valida as regras de negócio e chama os métodos deste repositório. 
Para o Frontend, os dados processados pelo Service são expostos via `UsuarioRouter` 
(endpoints REST), sendo consumidos pelo componente Angular `usuarios.component.ts`.
================================================================================
"""
from typing import Dict, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NivelUsuario, Usuario
from app.repositories.base_repository import BaseRepository

class UsuarioRepository(BaseRepository[Usuario]):
    """Acesso a dados de Usuario com isolamento por cliente (tenant) e filtros avançados."""

    def __init__(self, db: AsyncSession, cliente_id: Optional[int] = None):
        super().__init__(Usuario, db)
        self.cliente_id = cliente_id

    def _base_query(self):
        """Query base (select) já filtrada pelo tenant (cliente_id)."""
        stmt = select(Usuario)
        if self.cliente_id is not None:
            stmt = stmt.where(Usuario.cliente_id == self.cliente_id)
        return stmt

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário por email (escopo global, sem filtro de tenant)."""
        stmt = select(Usuario).where(Usuario.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, limit: int = 50, filtros: Optional[Dict] = None) -> Dict:
        """Lista usuários do tenant com paginação e filtros complexos."""
        filtros = filtros or {}
        stmt = self._base_query()

        if filtros.get("nivel"):
            stmt = stmt.join(NivelUsuario).where(NivelUsuario.nome == filtros["nivel"])
        if filtros.get("nivel_lista"):
            stmt = stmt.join(NivelUsuario).where(NivelUsuario.nome.in_(filtros["nivel_lista"]))
        if filtros.get("status"):
            stmt = stmt.where(Usuario.status == filtros["status"])
        if filtros.get("ativo") is not None:
            stmt = stmt.where(Usuario.ativo == filtros["ativo"])
        if filtros.get("search"):
            termo = f"%{filtros['search']}%"
            stmt = stmt.where(or_(Usuario.nome.ilike(termo), Usuario.email.ilike(termo)))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Usuario.nome.asc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        registros = result.scalars().all()

        return {"total": total, "page": page, "limit": limit, "data": registros}

    async def delete(self, usuario_id: int) -> bool:
        """Soft delete: desativa o usuário do tenant (sem commit direto)."""
        usuario = await self.get_by_id(usuario_id, self.cliente_id)
        if not usuario:
            return False
        usuario.ativo = False
        usuario.status = "inativo"
        await self.db.flush()
        return True