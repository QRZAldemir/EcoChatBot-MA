"""
================================================================================
PROJETO: EcoChatBotMarcx - Omnichannel SaaS
MÓDULO: base_repository.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Implementar a abstração genérica do padrão Repository (Repository Pattern) 
utilizando SQLAlchemy 2.0 e tipagem estática (Generics). Fornece operações 
CRUD assíncronas básicas, garantindo o princípio DRY (Don't Repeat Yourself) 
e a separação de responsabilidades (Unit of Work), onde o commit transacional 
é delegado à camada de Serviço.

ARQUITETURA E INTEGRAÇÃO:
Esta classe é a base da camada de acesso a dados (Data Access Layer). 
Ela NÃO é isolada; é projetada para ser herdada por todos os repositórios 
de domínio (ex: UsuarioRepository, ChamadaRepository). Ela não se comunica 
diretamente com o Frontend; seus dados são extraídos pelos Services, que 
por sua vez os expõem via Routers (FastAPI) para consumo do Frontend.
================================================================================
"""
from typing import TypeVar, Generic, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)

class BaseRepository(Generic[T]):
    """Repositório genérico assíncrono. Não gerencia transações (commit/rollback)."""
    
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int, cliente_id: Optional[int] = None) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        if cliente_id is not None and hasattr(self.model, 'cliente_id'):
            stmt = stmt.where(self.model.cliente_id == cliente_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj_in: T) -> T:
        self.db.add(obj_in)
        await self.db.flush()  # Flush prepara a transação sem dar commit definitivo
        await self.db.refresh(obj_in)
        return obj_in

    async def delete(self, id: int, cliente_id: Optional[int] = None, soft: bool = True) -> bool:
        obj = await self.get_by_id(id, cliente_id)
        if not obj:
            return False
        
        if soft and hasattr(obj, 'ativo'):
            obj.ativo = False
        else:
            stmt = delete(self.model).where(self.model.id == id)
            if cliente_id is not None:
                stmt = stmt.where(self.model.cliente_id == cliente_id)
            await self.db.execute(stmt)
            
        await self.db.flush()
        return True