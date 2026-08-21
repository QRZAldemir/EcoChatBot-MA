"""
Serviço de Atendimento — versão adaptada à arquitetura real do EcoChatBot-MA.

Usa os models definidos em app/models/__init__.py (Atendimento com status string,
sem cliente_id/deletado_em/paciente_*). O isolamento multi-tenant é feito via
filtro por departamento_id ou usuario_id do usuário autenticado quando aplicável.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session

from app.models import Atendimento, Departamento, Usuario
from app.schemas.atendimento import (
    FiltroAtendimento,
    AtendimentoCreate,
    AtendimentoUpdate,
    AtendimentoTransferir,
    AtendimentoFinalizar,
    AtendimentoIndicadores,
)


class AtendimentoService:
    """
    Serviço para gerenciar atendimentos.

    Args:
        db: Sessão do SQLAlchemy
    """

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # MÉTODOS PRIVADOS
    # ============================================

    def _get_base_query(self):
        """Retorna query base filtrando apenas atendimentos ativos."""
        return self.db.query(Atendimento).filter(Atendimento.ativo == True)

    def _apply_filters(self, query, filtros: FiltroAtendimento):
        """Aplica filtros à query."""
        if filtros.id:
            query = query.filter(Atendimento.id == filtros.id)

        if filtros.status:
            query = query.filter(Atendimento.status == filtros.status.value if hasattr(filtros.status, 'value') else filtros.status)

        if filtros.tipo_canal is not None:
            query = query.filter(Atendimento.tipo_canal == filtros.tipo_canal.value if hasattr(filtros.tipo_canal, 'value') else filtros.tipo_canal)

        if filtros.departamento_id:
            query = query.filter(Atendimento.departamento_id == filtros.departamento_id)

        if filtros.usuario_id:
            query = query.filter(Atendimento.usuario_id == filtros.usuario_id)

        if filtros.cliente_whatsapp:
            query = query.filter(Atendimento.telefone == filtros.cliente_whatsapp)

        if filtros.protocolo:
            query = query.filter(Atendimento.protocolo == filtros.protocolo)

        if filtros.data_inicio:
            query = query.filter(Atendimento.criado_em >= filtros.data_inicio)

        if filtros.data_fim:
            data_fim = filtros.data_fim + timedelta(days=1)
            query = query.filter(Atendimento.criado_em < data_fim)

        if filtros.ativo is not None:
            query = query.filter(Atendimento.ativo == filtros.ativo)

        return query

    @staticmethod
    def _gerar_protocolo() -> str:
        """Gera protocolo único para o atendimento."""
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        uid = uuid.uuid4().hex[:8].upper()
        return f"ECO-{timestamp}-{uid}"

    # ============================================
    # MÉTODOS PÚBLICOS
    # ============================================

    async def listar(
        self,
        filtros: Optional[FiltroAtendimento] = None,
        page: int = 1,
        limit: int = 50,
        order: str = "desc",
    ) -> Dict[str, Any]:
        """Lista atendimentos com filtros e paginação."""
        if not filtros:
            filtros = FiltroAtendimento()

        limit = min(limit, 100)
        offset = (page - 1) * limit

        query = self._get_base_query()
        query = self._apply_filters(query, filtros)

        total = query.count()

        order_by = desc(Atendimento.criado_em) if order == "desc" else asc(Atendimento.criado_em)
        query = query.order_by(order_by)

        registros = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "pagina": page,
            "limit": limit,
            "paginas": (total + limit - 1) // limit if total > 0 else 0,
            "registros": registros,
        }

    async def buscar_por_id(
        self,
        atendimento_id: int,
        usuario_id: Optional[int] = None,
    ) -> Atendimento:
        """Busca um atendimento por ID."""
        atendimento = (
            self._get_base_query()
            .filter(Atendimento.id == atendimento_id)
            .first()
        )

        if not atendimento:
            raise ValueError(f"Atendimento {atendimento_id} não encontrado")

        return atendimento

    async def criar(self, data: AtendimentoCreate) -> Atendimento:
        """Cria um novo atendimento."""
        if data.departamento_id:
            dept = self.db.query(Departamento).filter(
                Departamento.id == data.departamento_id,
                Departamento.ativo == True,
            ).first()
            if not dept:
                raise ValueError("Departamento não encontrado")

        atendimento = Atendimento(
            protocolo=self._gerar_protocolo(),
            telefone=data.paciente_telefone,
            nome_contato=data.paciente_nome,
            tipo_canal=data.tipo_canal.value if hasattr(data.tipo_canal, 'value') else data.tipo_canal,
            canal_id=data.canal_id,
            departamento_id=data.departamento_id,
            status="aberto",
            ativo=True,
            criado_em=datetime.utcnow(),
        )

        self.db.add(atendimento)
        self.db.commit()
        self.db.refresh(atendimento)

        return atendimento

    async def atualizar(
        self,
        atendimento_id: int,
        data: AtendimentoUpdate,
        usuario_id: Optional[int] = None,
    ) -> Atendimento:
        """Atualiza um atendimento existente."""
        atendimento = await self.buscar_por_id(atendimento_id, usuario_id)

        if atendimento.status == "finalizado":
            raise ValueError(f"Atendimento {atendimento_id} já está finalizado")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(atendimento, key):
                setattr(atendimento, key, value)

        atendimento.atualizado_em = datetime.utcnow()

        self.db.commit()
        self.db.refresh(atendimento)

        return atendimento

    async def transferir(
        self,
        atendimento_id: int,
        data: AtendimentoTransferir,
        usuario_id: int,
    ) -> Atendimento:
        """Transfere o atendimento para outro departamento/atendente."""
        atendimento = await self.buscar_por_id(atendimento_id, usuario_id)

        if atendimento.status == "finalizado":
            raise ValueError(f"Atendimento {atendimento_id} já está finalizado")

        if data.departamento_id is not None:
            dept = self.db.query(Departamento).filter(
                Departamento.id == data.departamento_id,
                Departamento.ativo == True,
            ).first()
            if not dept:
                raise ValueError("Departamento não encontrado")
            atendimento.departamento_id = data.departamento_id

        if data.usuario_id is not None:
            usuario = self.db.query(Usuario).filter(
                Usuario.id == data.usuario_id,
                Usuario.ativo == True,
            ).first()
            if not usuario:
                raise ValueError("Usuário não encontrado ou inativo")
            atendimento.usuario_id = data.usuario_id

        if data.canal_id is not None:
            atendimento.canal_id = data.canal_id

        # Atualiza status conforme atribuição
        if atendimento.usuario_id:
            atendimento.status = "em_atendimento"
        else:
            atendimento.status = "fila"

        atendimento.atualizado_em = datetime.utcnow()

        self.db.commit()
        self.db.refresh(atendimento)

        return atendimento

    async def finalizar(
        self,
        atendimento_id: int,
        data: Optional[AtendimentoFinalizar] = None,
        usuario_id: Optional[int] = None,
    ) -> Atendimento:
        """Finaliza um atendimento."""
        atendimento = await self.buscar_por_id(atendimento_id, usuario_id)

        if atendimento.status == "finalizado":
            raise ValueError(f"Atendimento {atendimento_id} já está finalizado")

        atendimento.status = "finalizado"
        atendimento.atualizado_em = datetime.utcnow()

        self.db.commit()
        self.db.refresh(atendimento)

        return atendimento

    async def indicadores(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> AtendimentoIndicadores:
        """Calcula indicadores em tempo real."""
        query = self._get_base_query()

        if data_inicio:
            query = query.filter(Atendimento.criado_em >= data_inicio)
        if data_fim:
            query = query.filter(Atendimento.criado_em <= data_fim + timedelta(days=1))

        total = query.count()
        aberto = query.filter(Atendimento.status == "aberto").count()
        fila = query.filter(Atendimento.status == "fila").count()
        em_atendimento = query.filter(Atendimento.status == "em_atendimento").count()
        finalizado_humano = query.filter(
            Atendimento.status == "finalizado",
            Atendimento.usuario_id.isnot(None),
        ).count()
        finalizado_sem_atendente = query.filter(
            Atendimento.status == "finalizado",
            Atendimento.usuario_id.is_(None),
        ).count()

        # Por departamento
        dept_rows = (
            query
            .outerjoin(Departamento, Atendimento.departamento_id == Departamento.id)
            .with_entities(
                Atendimento.departamento_id,
                func.coalesce(Departamento.nome, "Sem Departamento").label("nome"),
                func.count(Atendimento.id).label("total"),
            )
            .group_by(Atendimento.departamento_id, Departamento.nome)
            .all()
        )

        finalizados_por_depto = dict(
            query.filter(Atendimento.status == "finalizado")
            .with_entities(
                Atendimento.departamento_id,
                func.count(Atendimento.id),
            )
            .group_by(Atendimento.departamento_id)
            .all()
        )

        por_departamento = [
            {
                "departamento_id": dept_id,
                "nome": nome,
                "total": dept_total,
                "finalizados": finalizados_por_depto.get(dept_id, 0),
                "em_aberto": dept_total - finalizados_por_depto.get(dept_id, 0),
            }
            for dept_id, nome, dept_total in dept_rows
        ]
        por_departamento.sort(key=lambda d: d["total"], reverse=True)

        return AtendimentoIndicadores(
            total=total,
            aberto=aberto,
            fila=fila,
            em_atendimento=em_atendimento,
            finalizado_humano=finalizado_humano,
            finalizado_sem_atendente=finalizado_sem_atendente,
            por_departamento=por_departamento,
            tempo_medio_espera=None,
            tempo_medio_atendimento=None,
        )
