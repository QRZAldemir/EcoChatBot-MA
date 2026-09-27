# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.services.canais_multicanal_service
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-28
# VERSÃO: 1.0.0 (Lógica de Faturamento SaaS e Controle de Cotas)
# ==============================================================================
"""
FUNCIONALIDADE: Cálculo de faturamento SaaS, limites de cota e cobrança por 
                pontos de contato adicionais.
"""
import logging
from typing import Dict, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CanalContratado
from app.schemas.canal_schemas import CanalContratadoCreate
from app.services.canal_service import CanalService
from app.exceptions import RecursoInvalidoError, LimiteCotaExcedidoError

logger = logging.getLogger(__name__)

# Tabela de preços por tipo de canal (exemplo de regra de negócio)
PRECO_POR_CANAL = {
    "whatsapp": 49.90,
    "telegram": 29.90,
    "instagram": 39.90,
    "facebook": 39.90,
    "voip_telefonia": 59.90,
    "pabx": 59.90,
}

class CanaisMulticanalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.canal_service = CanalService(db)

    async def calcular_mensalidade_tenant(self, empresa_id: int) -> Dict[str, Any]:
        """
        Contabiliza a quantidade de canais de mídia ativos pertencentes ao tenant 
        e calcula o valor mensal do plano.
        """
        # Busca canais ativos e não deletados do tenant
        stmt = select(CanalContratado.tipo, func.count(CanalContratado.id)).where(
            CanalContratado.empresa_id == empresa_id,  # 🔒 TRAVA ANTI-IDOR
            CanalContratado.ativo == True,
            CanalContratado.deleted_at.is_(None)
        ).group_by(CanalContratado.tipo)
        
        resultados = (await self.db.execute(stmt)).all()
        
        total_canais = 0
        valor_total = 0.0
        detalhamento = {}

        for tipo, quantidade in resultados:
            preco_unitario = PRECO_POR_CANAL.get(tipo, 0.0)
            subtotal = quantidade * preco_unitario
            
            detalhamento[tipo] = {
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": subtotal
            }
            total_canais += quantidade
            valor_total += subtotal

        return {
            "empresa_id": empresa_id,
            "total_canais_ativos": total_canais,
            "valor_mensalidade_estimado": round(valor_total, 2),
            "detalhamento_por_tipo": detalhamento
        }

    async def criar_canal_com_validacao_de_cota(
        self, 
        dto: CanalContratadoCreate, 
        empresa_id: int, 
        limite_maximo_canais: int
    ) -> CanalContratado:
        """
        Cadastra o canal validando se o tenant atingiu a cota máxima do seu plano SaaS.
        """
        # 1. Contar canais ativos atuais do tenant
        stmt_count = select(func.count(CanalContratado.id)).where(
            CanalContratado.empresa_id == empresa_id,  # 🔒 TRAVA ANTI-IDOR
            CanalContratado.ativo == True,
            CanalContratado.deleted_at.is_(None)
        )
        total_atual = (await self.db.execute(stmt_count)).scalar() or 0

        # 2. Validar cota
        if total_atual >= limite_maximo_canais:
            raise LimiteCotaExcedidoError(
                f"Limite de canais atingido ({total_atual}/{limite_maximo_canais}). "
                "Faça o upgrade do seu plano para adicionar mais pontos de contato."
            )

        # 3. Se dentro da cota, delega a criação segura ao CanalService
        return await self.canal_service.criar_canal(dto, empresa_id)

    async def deletar_canal_e_recalcular_fatura(
        self, 
        canal_id: int, 
        empresa_id: int
    ) -> Dict[str, Any]:
        """
        Desativa o canal do tenant (soft delete) e retorna o novo cálculo da fatura mensal.
        """
        # 1. Deleta com segurança (o próprio método já valida o empresa_id)
        await self.canal_service.deletar_canal(canal_id, empresa_id)
        
        # 2. Recalcula a fatura imediatamente para refletir a mudança
        nova_fatura = await self.calcular_mensalidade_tenant(empresa_id)
        
        logger.info(f"Canal {canal_id} removido. Nova mensalidade da empresa {empresa_id}: {nova_fatura['valor_mensalidade_estimado']}")
        return nova_fatura