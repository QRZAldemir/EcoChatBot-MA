"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Canal Service — v2.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.canal_exceptions import (
    AcessoNegadoError,
    CanalNaoEncontradoError,
    CanalNomeDuplicadoError,
    CanalSemTelefoneError,
    CanalTipoInvalidoError,
    RecursoInvalidoError,
)
from app.models.canal_contratado_models import CanalContratado
from app.schemas.canal_schemas import (
    CHAVE_IDENTIFICADOR,
    CanalContratadoCreate,
    CanalContratadoUpdate,
    TipoCanal,
)

logger = logging.getLogger(__name__)

#: Lista canônica de tipos aceitos (espelha TipoCanal do schema).
TIPOS_VALIDOS: frozenset[str] = frozenset(TipoCanal.__args__)


class CanalService:
    """Service de gestão dos canais contratados do tenant."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════
    @staticmethod
    def _agora() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _validar_empresa_id(empresa_id: int | None) -> int:
        if not empresa_id:
            raise AcessoNegadoError("empresa_id é obrigatório (multi-tenant).")
        return empresa_id

    @staticmethod
    def _serializar_credenciais(dados: dict) -> None:
        """
        Converte `identificador` em `credenciais[CHAVE_IDENTIFICADOR[tipo]]`
        e serializa em JSON (Text no banco).

        Muta `dados` in-place.
        """
        tipo = dados.get("tipo")
        identificador = dados.pop("identificador", None)

        credenciais = dados.get("credenciais")

        if identificador is not None:
            if tipo not in TIPOS_VALIDOS:
                raise CanalTipoInvalidoError(f"Tipo '{tipo}' não suportado.")
            chave = CHAVE_IDENTIFICADOR.get(tipo, "identificador")
            credenciais = dict(credenciais or {})
            credenciais[chave] = identificador

        if credenciais is not None:
            dados["credenciais"] = json.dumps(credenciais, ensure_ascii=False)

    @staticmethod
    def _desserializar_credenciais(canal: CanalContratado) -> dict | None:
        """Converte `credenciais` Text → dict em memória (sem persistir)."""
        if not canal.credenciais:
            return None
        try:
            return json.loads(canal.credenciais)
        except (TypeError, ValueError):
            logger.warning("credenciais inválidas no canal %s", canal.id)
            return None

    async def _get_do_tenant(
        self,
        canal_id: int,
        empresa_id: int,
        *,
        incluir_inativos: bool = False,
    ) -> CanalContratado:
        """🔒 Anti-IDOR: filtra obrigatoriamente por empresa_id."""
        self._validar_empresa_id(empresa_id)

        stmt = select(CanalContratado).where(
            CanalContratado.id == canal_id,
            CanalContratado.empresa_id == empresa_id,   # 🔒
            CanalContratado.deleted_at.is_(None),
        )
        if not incluir_inativos:
            stmt = stmt.where(CanalContratado.ativo.is_(True))

        canal = (await self.db.execute(stmt)).scalar_one_or_none()
        if canal is None:
            raise CanalNaoEncontradoError(
                f"Canal id={canal_id} não encontrado para o tenant atual."
            )
        return canal

    async def _validar_unicidade_tipo_telefone(
        self,
        telefone_id: int,
        tipo: str,
        empresa_id: int,
        *,
        ignorar_canal_id: int | None = None,
    ) -> None:
        stmt = select(CanalContratado.id).where(
            CanalContratado.empresa_id == empresa_id,       # 🔒
            CanalContratado.telefone_id == telefone_id,
            CanalContratado.tipo == tipo,
            CanalContratado.deleted_at.is_(None),
        )
        if ignorar_canal_id is not None:
            stmt = stmt.where(CanalContratado.id != ignorar_canal_id)

        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise CanalNomeDuplicadoError(
                f"Já existe um canal do tipo '{tipo}' vinculado a este telefone."
            )

    # ══════════════════════════════════════════════════════════════════════
    # LEITURA
    # ══════════════════════════════════════════════════════════════════════
    async def listar_canais(
        self,
        empresa_id: int,
        apenas_ativos: bool = True,
    ) -> list[CanalContratado]:
        self._validar_empresa_id(empresa_id)

        stmt = select(CanalContratado).where(
            CanalContratado.empresa_id == empresa_id,   # 🔒
            CanalContratado.deleted_at.is_(None),
        )
        if apenas_ativos:
            stmt = stmt.where(CanalContratado.ativo.is_(True))

        stmt = stmt.order_by(CanalContratado.id.asc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def buscar_por_id(
        self, canal_id: int, empresa_id: int,
    ) -> CanalContratado | None:
        self._validar_empresa_id(empresa_id)
        try:
            return await self._get_do_tenant(canal_id, empresa_id)
        except CanalNaoEncontradoError:
            return None

    # ══════════════════════════════════════════════════════════════════════
    # CRIAÇÃO
    # ══════════════════════════════════════════════════════════════════════
    async def criar_canal(
        self,
        dto: CanalContratadoCreate,
        empresa_id: int,
    ) -> CanalContratado:
        self._validar_empresa_id(empresa_id)

        dados = dto.model_dump(exclude_unset=True)
        dados.pop("empresa_id", None)   # 🔒
        dados.pop("cliente_id", None)   # 🔒

        # Regra de negócio: canal SEM telefone → 403
        if not dados.get("telefone_id"):
            raise CanalSemTelefoneError(
                "Todo canal precisa estar vinculado a um telefone."
            )

        self._serializar_credenciais(dados)

        await self._validar_unicidade_tipo_telefone(
            telefone_id=dados["telefone_id"],
            tipo=dados["tipo"],
            empresa_id=empresa_id,
        )

        canal = CanalContratado(**dados, empresa_id=empresa_id)
        canal.ativo = dados.get("ativo", True)

        self.db.add(canal)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            logger.warning("Violação de unicidade: %s", exc)
            raise CanalNomeDuplicadoError(
                "Já existe um canal desse tipo para este telefone."
            ) from exc

        await self.db.refresh(canal)
        logger.info("Canal criado: id=%s tipo=%s empresa=%s",
                    canal.id, canal.tipo, empresa_id)
        return canal

    # ══════════════════════════════════════════════════════════════════════
    # ATUALIZAÇÃO
    # ══════════════════════════════════════════════════════════════════════
    async def atualizar_canal(
        self,
        canal_id: int,
        dto: CanalContratadoUpdate,
        empresa_id: int,
    ) -> CanalContratado:
        self._validar_empresa_id(empresa_id)

        canal = await self._get_do_tenant(canal_id, empresa_id)  # 🔒

        dados = dto.model_dump(exclude_unset=True)
        dados.pop("empresa_id", None)
        dados.pop("cliente_id", None)
        dados.pop("id", None)

        self._serializar_credenciais(dados)

        novo_telefone = dados.get("telefone_id", canal.telefone_id)
        novo_tipo = dados.get("tipo", canal.tipo)
        if novo_telefone != canal.telefone_id or novo_tipo != canal.tipo:
            await self._validar_unicidade_tipo_telefone(
                telefone_id=novo_telefone,
                tipo=novo_tipo,
                empresa_id=empresa_id,
                ignorar_canal_id=canal.id,
            )

        for campo, valor in dados.items():
            setattr(canal, campo, valor)

        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise CanalNomeDuplicadoError(
                "Atualização viola a unicidade (telefone_id, tipo)."
            ) from exc

        await self.db.refresh(canal)
        return canal

    # ══════════════════════════════════════════════════════════════════════
    # EXCLUSÃO (soft delete)
    # ══════════════════════════════════════════════════════════════════════
    async def deletar_canal(self, canal_id: int, empresa_id: int) -> bool:
        self._validar_empresa_id(empresa_id)
        canal = await self._get_do_tenant(
            canal_id, empresa_id, incluir_inativos=True,
        )  # 🔒

        canal.ativo = False
        canal.deleted_at = self._agora()

        await self.db.commit()
        logger.info("Canal desativado: id=%s empresa=%s", canal.id, empresa_id)
        return True

    # ══════════════════════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ══════════════════════════════════════════════════════════════════════
    async def contar_canais_ativos(self, empresa_id: int) -> int:
        self._validar_empresa_id(empresa_id)
        stmt = select(func.count(CanalContratado.id)).where(
            CanalContratado.empresa_id == empresa_id,   # 🔒
            CanalContratado.ativo.is_(True),
            CanalContratado.deleted_at.is_(None),
        )
        return int((await self.db.execute(stmt)).scalar_one() or 0)

    async def contar_por_tipo(self, empresa_id: int) -> dict[str, int]:
        self._validar_empresa_id(empresa_id)
        stmt = (
            select(CanalContratado.tipo, func.count(CanalContratado.id))
            .where(
                CanalContratado.empresa_id == empresa_id,   # 🔒
                CanalContratado.ativo.is_(True),
                CanalContratado.deleted_at.is_(None),
            )
            .group_by(CanalContratado.tipo)
        )
        rows = (await self.db.execute(stmt)).all()
        return {str(tipo): int(qtd) for tipo, qtd in rows}

    # ─── Helpers públicos para o billing ────────────────────────────────
    def credenciais_em_dict(self, canal: CanalContratado) -> dict | None:
        """Expõe o helper de desserialização para o billing/outros services."""
        return self._desserializar_credenciais(canal)


__all__ = ["CanalService", "TIPOS_VALIDOS"]