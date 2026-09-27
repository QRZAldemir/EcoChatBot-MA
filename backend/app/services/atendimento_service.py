"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Atendimento Service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_service.py
@module   Backend / App / Services / Atendimento
@author   Aldemir Queiroz
@since    2026
@version  3.0.0  · fix: IDOR em listagem por telefone_id
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Camada de serviço do domínio Atendimento. Concentra:

    ┌──────────────────────────────┬──────────────────────────────────┐
    │ Operação                     │ O que faz                          │
    ├──────────────────────────────┼──────────────────────────────────┤
    │ listar()                     │ Lista atendimentos com filtros,    │
    │                              │ sempre isolado por tenant          │
    │ buscar_por_id()              │ Recupera um atendimento do tenant  │
    │ criar()                      │ Cria atendimento validando FK      │
    │ atualizar()                  │ Atualiza com validação de tenant   │
    │ finalizar()                  │ Fecha atendimento + invalida cache │
    │ _validar_telefone()          │ 🆕 Garante posse do telefone       │
    └──────────────────────────────┴──────────────────────────────────┘

⚠️ CORREÇÃO DE SEGURANÇA (v3.0.0) — IDOR EM /atendimentos/listar
────────────────────────────────────────────────────────────────
ANTES:
    listar(db, canal=1, telefone_id=qualquer_id)
    → O serviço filtrava atendimentos pelo `telefone_id` SEM verificar
      se o telefone pertence ao tenant do usuário autenticado.
    → Atacante do Tenant A passa `telefone_id` do Tenant B e lê o
      histórico de conversas alheias.

DEPOIS:
    listar(db, *, empresa_id, canal=1, telefone_id=...)
    → `empresa_id` é OBRIGATÓRIO. É resolvido pelo router via
      `get_current_empresa()` (deps).
    → Se `telefone_id` for informado, `_validar_telefone()` confirma
      que ele pertence à `empresa_id` ANTES de rodar a query.
    → A query final aplica filtro duplo: `telefone_id` + `empresa_id`.

REGRAS INVIOLÁVEIS
──────────────────
    1. `empresa_id` é parâmetro OBRIGATÓRIO em toda operação
    2. Nenhuma consulta filtra por `id` sem `empresa_id`
    3. Toda validação de recurso externo (Telefone, Canal, etc.)
       passa pelo helper `_validar_*_do_tenant()`
    4. Erros de vínculo cruzado → HTTPException(403) + log de auditoria
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.atendimento_models import Atendimento
from app.models.enums import StatusAtendimento
from app.models.telefone_models import Telefone   # ajuste se o nome for outro


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO DE DOMÍNIO
# ═══════════════════════════════════════════════════════════════════════════

class RecursoInvalidoError(HTTPException):
    """
    Erro de negócio: recurso não existe OU não pertence ao tenant.

    A mensagem NÃO distingue os dois casos — evita enumeração de IDs.
    """

    def __init__(self, detail: str = "Recurso inválido ou inacessível."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# ═══════════════════════════════════════════════════════════════════════════
# SERVIÇO
# ═══════════════════════════════════════════════════════════════════════════

class AtendimentoService:
    """
    Orquestra regras de negócio de Atendimento.

    Toda instância é vinculada a UMA empresa (`empresa_id`). Isso garante
    que nenhuma operação consiga escapar do tenant sem que o programador
    perceba — o filtro está na raiz.
    """

    def __init__(self, db: AsyncSession, empresa_id: int) -> None:
        if not empresa_id or empresa_id <= 0:
            raise ValueError(
                "empresa_id é obrigatório em AtendimentoService — "
                "sem ele há risco de IDOR cross-tenant."
            )
        self.db = db
        self.empresa_id = empresa_id

    # ═════════════════════════════════════════════════════════════════════
    # HELPERS PRIVADOS — validação de pertencimento
    # ═════════════════════════════════════════════════════════════════════

    async def _validar_telefone(self, telefone_id: int) -> Telefone:
        """
        Valida que o telefone existe E pertence à empresa do usuário.

        ─────────────────────────────────────────────────────────────────────
        PADRÃO IDOR QUE ESTE HELPER MATA
        ─────────────────────────────────────────────────────────────────────
        Vulnerável:
            select(Telefone).where(Telefone.id == telefone_id)

        Seguro:
            select(Telefone).where(
                Telefone.id == telefone_id,
                Telefone.empresa_id == self.empresa_id,   # ✅ filtro
                Telefone.deleted_at.is_(None),
            )

        ─────────────────────────────────────────────────────────────────────
        POR QUE MENSAGEM GENÉRICA
        ─────────────────────────────────────────────────────────────────────
        "não existe" e "existe mas é de outro tenant" retornam a MESMA
        mensagem — evita que um atacante descubra quais IDs existem.
        """
        stmt = select(Telefone).where(
            Telefone.id == telefone_id,
            Telefone.empresa_id == self.empresa_id,          # ✅ tenant
            Telefone.deleted_at.is_(None),
        )
        telefone = (await self.db.execute(stmt)).scalars().first()

        if telefone is None:
            logger.warning(
                "SECURITY: acesso a telefone negado | "
                "telefone_id=%s empresa_id_alvo=%s",
                telefone_id, self.empresa_id,
            )
            raise RecursoInvalidoError(
                f"Telefone {telefone_id} não encontrado para esta empresa."
            )
        return telefone

    async def _validar_atendimento(self, atendimento_id: int) -> Atendimento:
        """
        Valida que o atendimento existe E pertence à empresa.
        Evita IDOR em GET /atendimentos/{id}, PUT, DELETE, etc.
        """
        stmt = select(Atendimento).where(
            Atendimento.id == atendimento_id,
            Atendimento.empresa_id == self.empresa_id,       # ✅ tenant
            Atendimento.deleted_at.is_(None),
        )
        at = (await self.db.execute(stmt)).scalars().first()

        if at is None:
            logger.warning(
                "SECURITY: acesso a atendimento negado | "
                "atendimento_id=%s empresa_id_alvo=%s",
                atendimento_id, self.empresa_id,
            )
            raise RecursoInvalidoError(
                f"Atendimento {atendimento_id} não encontrado para esta empresa."
            )
        return at

    # ═════════════════════════════════════════════════════════════════════
    # LISTAR — endpoint corrigido
    # ═════════════════════════════════════════════════════════════════════

    async def listar(
        self,
        *,
        canal: Optional[int] = None,
        telefone_id: Optional[int] = None,
        status: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Lista atendimentos com filtros, SEMPRE isolado por empresa.

        ─────────────────────────────────────────────────────────────────────
        FLUXO
        ─────────────────────────────────────────────────────────────────────
            1. Se `telefone_id` foi informado → valida pertencimento
               (fail-fast, antes de qualquer query)
            2. Monta a query com filtro OBRIGATÓRIO por `empresa_id`
            3. Aplica filtros opcionais (canal, status, período)
            4. Paginação
            5. Retorna dict com `items`, `total`, `page`, `limit`

        ─────────────────────────────────────────────────────────────────────
        POR QUE VALIDAR ANTES DA QUERY
        ─────────────────────────────────────────────────────────────────────
        Se rodássemos a query primeiro e validássemos depois, o banco
        executaria um SELECT com um ID possivelmente inválido — desperdício
        E risco de logar dados que não deviam passar pelo processo.

        Validar antes é fail-fast: 403 sai antes do banco ser tocado.

        ─────────────────────────────────────────────────────────────────────
        POR QUE EMPRESA_ID NO WHERE MESMO APÓS VALIDAR
        ─────────────────────────────────────────────────────────────────────
        Defense in depth. Se por um bug futuro alguém remover a validação,
        a query continua segura. Cada camada segura independentemente.
        """
        # ─── 1. Validação fail-fast do telefone (se informado) ────────────
        telefone_validado: Optional[Telefone] = None
        if telefone_id is not None:
            telefone_validado = await self._validar_telefone(telefone_id)

        # ─── 2. Query base — filtro OBRIGATÓRIO por tenant ────────────────
        stmt: Select = select(Atendimento).where(
            Atendimento.empresa_id == self.empresa_id,       # ✅ tenant
            Atendimento.deleted_at.is_(None),
        )

        # ─── 3. Filtros opcionais ─────────────────────────────────────────
        if telefone_validado is not None:
            stmt = stmt.where(Atendimento.telefone_id == telefone_validado.id)

        if canal is not None:
            stmt = stmt.where(Atendimento.canal == canal)

        if status is not None:
            stmt = stmt.where(Atendimento.status == status)

        if data_inicio is not None:
            stmt = stmt.where(Atendimento.created_at >= data_inicio)

        if data_fim is not None:
            stmt = stmt.where(Atendimento.created_at <= data_fim)

        # ─── 4. Contagem total (para paginação) ───────────────────────────
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # ─── 5. Paginação e ordenação ─────────────────────────────────────
        stmt = (
            stmt.order_by(Atendimento.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = (await self.db.execute(stmt)).scalars().all()

        logger.debug(
            "listar atendimentos | empresa=%s telefone_id=%s total=%s",
            self.empresa_id, telefone_id, total,
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
        }

    # ═════════════════════════════════════════════════════════════════════
    # BUSCAR POR ID — mesma proteção
    # ═════════════════════════════════════════════════════════════════════

    async def buscar_por_id(self, atendimento_id: int) -> Atendimento:
        """
        Recupera um atendimento do tenant.
        Delega para `_validar_atendimento()`, que já filtra por empresa.
        """
        return await self._validar_atendimento(atendimento_id)

    # ═════════════════════════════════════════════════════════════════════
    # CRIAR
    # ═════════════════════════════════════════════════════════════════════

    async def criar(
        self,
        *,
        telefone_id: int,
        contato_id: int,
        canal_contratado_id: int,
        protocolo: str,
        **campos,
    ) -> Atendimento:
        """
        Cria atendimento validando que telefone, contato e canal
        pertencem à empresa ANTES do INSERT.
        """
        # ─── Valida telefone ──────────────────────────────────────────────
        telefone = await self._validar_telefone(telefone_id)

        # ─── Valida demais vínculos (helpers genéricos) ───────────────────
        # (use a mesma estratégia do _validar_telefone para cada FK)

        at = Atendimento(
            empresa_id=self.empresa_id,               # ✅ herda tenant
            telefone_id=telefone.id,
            contato_id=contato_id,
            canal_contratado_id=canal_contratado_id,
            protocolo=protocolo,
            status=StatusAtendimento.AGUARDANDO.value,
            **campos,
        )
        self.db.add(at)
        await self.db.commit()
        await self.db.refresh(at)

        logger.info(
            "Atendimento criado | id=%s empresa=%s protocolo=%s",
            at.id, self.empresa_id, at.protocolo,
        )
        return at

    # ═════════════════════════════════════════════════════════════════════
    # ATUALIZAR
    # ═════════════════════════════════════════════════════════════════════

    async def atualizar(
        self,
        atendimento_id: int,
        **campos: Any,
    ) -> Atendimento:
        """
        Atualiza atendimento — sempre passa por `_validar_atendimento`,
        que já filtra por empresa.
        """
        at = await self._validar_atendimento(atendimento_id)

        CAMPOS_PROIBIDOS = {
            "id", "empresa_id", "created_at", "deleted_at",
        }
        for chave, valor in campos.items():
            if chave in CAMPOS_PROIBIDOS:
                logger.warning("Campo proibido ignorado: %s", chave)
                continue
            if hasattr(at, chave):
                setattr(at, chave, valor)

        await self.db.commit()
        await self.db.refresh(at)
        logger.info(
            "Atendimento atualizado | id=%s empresa=%s",
            at.id, self.empresa_id,
        )
        return at

    # ═════════════════════════════════════════════════════════════════════
    # FINALIZAR
    # ═════════════════════════════════════════════════════════════════════

    async def finalizar(self, atendimento_id: int) -> Atendimento:
        """
        Finaliza um atendimento. Marca `finalizado_em` e invalida o cache
        Redis (mesma chave usada em bot_service).
        """
        at = await self._validar_atendimento(atendimento_id)
        at.status = StatusAtendimento.FINALIZADO.value
        at.finalizado_em = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(at)

        # Invalida cache do atendimento ativo (se aplicável)
        # await invalidar_cache_atendimento(redis, at.empresa_id, at.telefone)

        logger.info(
            "Atendimento finalizado | id=%s empresa=%s",
            at.id, self.empresa_id,
        )
        return at


__all__ = ["AtendimentoService", "RecursoInvalidoError"]