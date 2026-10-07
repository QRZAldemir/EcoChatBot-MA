"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: base_repository.py
AUTOR: Aldemir Queiroz
DATA: 2026-10-07
================================================================================
PROPÓSITO:
Implementar a abstração genérica do padrão Repository utilizando SQLAlchemy 2.0 
e tipagem estática (Generics). Fornece operações CRUD assíncronas básicas, 
garantindo o princípio DRY e a separação de responsabilidades (Unit of Work).
A camada de Serviço é responsável pelo commit/rollback transacional.
================================================================================
"""
from typing import TypeVar, Generic, Type, Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)

class BaseRepository(Generic[T]):
    """Repositório genérico assíncrono com travas de segurança multi-tenant."""
    
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db
        # Detecta dinamicamente o campo de isolamento (empresa_id ou cliente_id)
        self.tenant_field = 'empresa_id' if hasattr(self.model, 'empresa_id') else 'cliente_id'

    def _get_tenant_filter(self, cliente_id: int):
        """Retorna a condição de filtro de tenant para evitar vazamento de dados (Anti-IDOR)."""
        return getattr(self.model, self.tenant_field) == cliente_id

    async def get_by_id(self, id: int, cliente_id: int) -> Optional[T]:
        """Busca por ID com trava Anti-IDOR."""
        stmt = select(self.model).where(
            self.model.id == id,
            self._get_tenant_filter(cliente_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, dto: Any, cliente_id: int) -> T:
        """Persiste nova entidade atribuindo obrigatoriamente o tenant."""
        # Suporte flexível a Pydantic v2, v1 ou dicionários puros
        if hasattr(dto, 'model_dump'):
            obj_data = dto.model_dump(exclude_unset=True)
        elif hasattr(dto, 'dict'):
            obj_data = dto.dict(exclude_unset=True)
        else:
            obj_data = dto
            
        obj_data[self.tenant_field] = cliente_id
        obj_in = self.model(**obj_data)
        
        self.db.add(obj_in)
        await self.db.flush()
        await self.db.refresh(obj_in)
        return obj_in

    async def update(self, id: int, dto: Any, cliente_id: int) -> Optional[T]:
        """Atualização parcial segura com verificação prévia de tenant."""
        obj = await self.get_by_id(id, cliente_id)
        if not obj:
            return None
        
        if hasattr(dto, 'model_dump'):
            obj_data = dto.model_dump(exclude_unset=True)
        elif hasattr(dto, 'dict'):
            obj_data = dto.dict(exclude_unset=True)
        else:
            obj_data = dto
            
        for field, value in obj_data.items():
            # Previne sobrescrita maliciosa ou acidental do campo de tenant
            if hasattr(obj, field) and field != self.tenant_field:
                setattr(obj, field, value)
                
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int, cliente_id: int, soft: bool = True) -> bool:
        """Soft-delete (exclusão lógica) ou exclusão física com verificação de tenant."""
        obj = await self.get_by_id(id, cliente_id)
        if not obj:
            return False
        
        if soft and hasattr(obj, 'ativo'):
            obj.ativo = False
            await self.db.flush()
            await self.db.refresh(obj)
        else:
            stmt = delete(self.model).where(
                self.model.id == id,
                self._get_tenant_filter(cliente_id)
            )
            await self.db.execute(stmt)
            await self.db.flush()
        return True

    async def listar(self, cliente_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        """Listagem paginada e ordenada por empresa."""
        stmt = select(self.model).where(self._get_tenant_filter(cliente_id))
        
        # Ordenação padrão por ID decrescente (registros mais recentes primeiro)
        if hasattr(self.model, 'id'):
            stmt = stmt.order_by(self.model.id.desc())
            
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def contar(self, cliente_id: int) -> int:
        """Contagem total de registros do tenant."""
        stmt = select(func.count()).select_from(self.model).where(
            self._get_tenant_filter(cliente_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0