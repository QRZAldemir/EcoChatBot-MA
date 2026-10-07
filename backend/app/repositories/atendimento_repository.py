"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: atendimento_repository.py
AUTOR: Aldemir Queiroz
DATA: 2026-10-07
================================================================================
PROPÓSITO:
Implementar a camada de acesso a dados específica para a entidade Atendimento.
Estende BaseRepository para herdar o CRUD genérico seguro e adiciona métodos 
de negócio relacionados a sessões de chat, protocolos e métricas de fila.
================================================================================
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.atendimento_models import Atendimento
from app.models.contato_models import Contato
from app.models.enums import StatusAtendimento
from app.repositories.base_repository import BaseRepository

class AtendimentoRepository(BaseRepository[Atendimento]):
    """Repositório para gestão de atendimentos, sessões de chat e métricas."""

    def __init__(self, db: AsyncSession):
        super().__init__(Atendimento, db)

    async def em_aberto(self, telefone: str, cliente_id: int) -> Optional[Atendimento]:
        """
        Busca sessão ativa para o contato.
        Considera status que indicam que o atendimento ainda não foi concluído.
        """
        status_aberto = [
            StatusAtendimento.AGUARDANDO.value,
            StatusAtendimento.EM_ANDAMENTO.value,
            StatusAtendimento.PAUSADO.value,
            StatusAtendimento.TRANSFERIDO.value
        ]
        
        stmt = (
            select(Atendimento)
            .join(Contato, Atendimento.contato_id == Contato.id)
            .where(Contato.telefone == telefone)
            .where(Atendimento.status.in_(status_aberto))
            .where(self._get_tenant_filter(cliente_id))
            .order_by(Atendimento.iniciado_em.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def por_protocolo(self, protocolo: str, cliente_id: int) -> Optional[Atendimento]:
        """Localiza atendimento pelo código único com trava de tenant."""
        stmt = (
            select(Atendimento)
            .where(Atendimento.protocolo == protocolo)
            .where(self._get_tenant_filter(cliente_id))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_periodo(
        self, 
        cliente_id: int, 
        data_inicio: datetime, 
        data_fim: datetime, 
        status: Optional[str] = None
    ) -> List[Atendimento]:
        """
        Suporte aos relatórios, filtrando por período e opcionalmente por status.
        Ordenado do mais recente para o mais antigo.
        """
        stmt = select(Atendimento).where(
            self._get_tenant_filter(cliente_id),
            Atendimento.iniciado_em >= data_inicio,
            Atendimento.iniciado_em <= data_fim
        )
        if status:
            stmt = stmt.where(Atendimento.status == status)
            
        stmt = stmt.order_by(Atendimento.iniciado_em.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def contar_por_status(self, cliente_id: int) -> dict:
        """
        Métrica de fila (Aguardando / Em Atendimento / Finalizado).
        Retorna um dicionário com a contagem agrupada por status para dashboards.
        """
        stmt = (
            select(Atendimento.status, func.count(Atendimento.id))
            .where(self._get_tenant_filter(cliente_id))
            .group_by(Atendimento.status)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Inicializa métricas com zero para garantir consistência na resposta
        metrics = {
            "aguardando": 0,
            "em_andamento": 0,
            "pausado": 0,
            "transferido": 0,
            "finalizado": 0,
            "cancelado": 0,
            "total": 0
        }
        
        for status, count in rows:
            if status in metrics:
                metrics[status] = count
            metrics["total"] += count
            
        return metrics