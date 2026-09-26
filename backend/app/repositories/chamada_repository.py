"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: repositories/chamada_repository.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Acesso a dados da entidade `Chamada`. Segue estritamente o padrão Unit of Work,
onde o `flush()` prepara a transação, mas o `commit()` é delegado ao Service.

ARQUITETURA E INTEGRAÇÃO:
Camada de Acesso a Dados. Herda de `BaseRepository`. Injetado no `PabxService`.
================================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chamada import Chamada
from app.repositories.base_repository import BaseRepository

class ChamadaRepository(BaseRepository[Chamada]):
    def __init__(self, db: AsyncSession):
        super().__init__(Chamada, db)