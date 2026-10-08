"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Canais Multicanal Service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     canais_multicanal_service.py
@module   Backend / App / Services / Canais Multicanal
@author   Aldemir Queiroz
@since    2026
@version  2.0.0 (Faturamento SaaS + Controle de Cota)
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
• Cálculo da mensalidade do tenant com base nos canais ATIVOS contratados.
• Validação de cota antes de permitir a criação de um novo canal.
• Recálculo de fatura após exclusão (soft delete) de canal.

🔒 ANTI-IDOR
────────────
Todo cálculo é filtrado por `empresa_id`. Nenhum agregado é exposto de
outra empresa.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import LimiteCotaExcedidoError, RecursoInvalidoError
from app.models.canal_models import CanalContratado
from app.schemas.canal_schemas import CanalContratadoCreate
from app.services.canal_service import CanalService

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# TABELA DE PREÇOS POR TIPO DE CANAL
# ────────────────────────────────────────────────────────────────────────────
# TODO: mover para app/core/config.py ou para tabela `planos_saas` quando
#       a entidade `PlanoSaaS` for implementada.
PRECO_POR_CANAL: dict[str, float] = {
    "whatsapp":       49.90,
    "telegram":       29.90,
    "instagram":      39.90,
    "facebook":       39.90,
    "voip_telefonia": 59.90,
    "pabx":           59.90,
    "discord":        29.90,
    "email":          19.90,
}


class CanaisMulticanalService:
    """
    Service de faturamento SaaS e controle de cota do tenant.

    Uso típico (router):

        service = CanaisMulticanalService(db)
        fatura = await service.calcular_mensalidade_tenant(empresa_id)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.canal_service = CanalService(db)

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS INTERNOS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _validar_empresa_id(empresa_id: int | None) -> int:
        if not empresa_id:
            raise RecursoInvalidoError("empresa_id é obrigatório.")
        return empresa_id

    @staticmethod
   

    # ══════════════════════════════════════════════════════════════════════
    # FATURAMENTO
    # ══════════════════════════════════════════════════════════════════════

    async def calcular_mensalidade_tenant(
        self,
        empresa_id: int,
    ) -> dict[str, Any]:
        """
        Contabiliza os canais ativos do tenant e calcula o valor mensal.

        Retorna:
            {
                "empresa_id": int,
                "total_canais_ativos": int,
                "valor_mensalidade_estimado": float,
                "detalhamento_por_tipo": {
                    "<tipo>": {
                        "quantidade": int,
                        "preco_unitario": float,
                        "subtotal": float,
                    },
                    ...
                }
            }

        🔒 Anti-IDOR: filtro obrigatório por `empresa_id`.
        """
        self._validar_empresa_id(empresa_id)

        stmt = (
            select(CanalContratado.tipo, func.count(CanalContratado.id))
            .where(
                CanalContratado.empresa_id == empresa_id,   # 🔒 Anti-IDOR
                CanalContratado.ativo.is_(True),
                CanalContratado.deleted_at.is_(None),
            )
            .group_by(CanalContratado.tipo)
        )
        resultados = (await self.db.execute(stmt)).all()

        total_canais = 0
        valor_total = 0.0
        detalhamento: dict[str, dict[str, Any]] = {}

        for tipo_raw, quantidade in resultados:
            tipo = self._normalizar_tipo(tipo_raw)
            preco_unitario = PRECO_POR_CANAL.get(tipo, 0.0)
            subtotal = round(quantidade * preco_unitario, 2)

            detalhamento[tipo] = {
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": subtotal,
            }
            total_canais += quantidade
            valor_total += subtotal

        return {
            "empresa_id": empresa_id,
            "total_canais_ativos": total_canais,
            "valor_mensalidade_estimado": round(valor_total, 2),
            "detalhamento_por_tipo": detalhamento,
        }

    # ══════════════════════════════════════════════════════════════════════
    # CRIAÇÃO COM VALIDAÇÃO DE COTA
    # ══════════════════════════════════════════════════════════════════════

    async def criar_canal_com_validacao_de_cota(
        self,
        dto: CanalContratadoCreate,
        empresa_id: int,
        limite_maximo_canais: int,
    ) -> CanalContratado:
        """
        Cadastra o canal validando a cota do plano SaaS do tenant.

        Args:
            dto: Payload de criação (Pydantic v2).
            empresa_id: Tenant autenticado.
            limite_maximo_canais: Cota contratada.
                TODO: substituir por `PlanoSaaS.limite_canais` quando existir.

        Raises:
            LimiteCotaExcedidoError: Se o tenant já atingiu a cota.

        🔒 Anti-IDOR: o `empresa_id` nunca vem do DTO.
        """
        self._validar_empresa_id(empresa_id)

        total_atual = await self.canal_service.contar_canais_ativos(empresa_id)

        if total_atual >= limite_maximo_canais:
            raise LimiteCotaExcedidoError(
                f"Limite de canais atingido ({total_atual}/{limite_maximo_canais}). "
                "Faça o upgrade do seu plano para adicionar mais pontos de contato."
            )

        # Delega ao CanalService (que já aplica Anti-IDOR + unicidade)
        return await self.canal_service.criar_canal(dto, empresa_id)

    # ══════════════════════════════════════════════════════════════════════
    # DELETE + RECÁLCULO
    # ══════════════════════════════════════════════════════════════════════

    async def deletar_canal_e_recalcular_fatura(
        self,
        canal_id: int,
        empresa_id: int,
    ) -> dict[str, Any]:
        """
        Desativa o canal (soft delete) e retorna o novo cálculo da fatura.

        🔒 Anti-IDOR: delegação ao CanalService já valida `empresa_id`.
        """
        self._validar_empresa_id(empresa_id)

        await self.canal_service.deletar_canal(canal_id, empresa_id)

        nova_fatura = await self.calcular_mensalidade_tenant(empresa_id)

        logger.info(
            "Canal %s removido. Nova mensalidade da empresa %s: R$ %s",
            canal_id, empresa_id, nova_fatura["valor_mensalidade_estimado"],
        )
        return nova_fatura


__all__ = ["CanaisMulticanalService", "PRECO_POR_CANAL"]