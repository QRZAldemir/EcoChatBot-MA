"""
Serviço de Atendimento — versão adaptada à arquitetura real do EcoChatBot-MA.

Usa os models definidos em app/models/__init__.py (Atendimento com status string,
sem cliente_id/deletado_em/paciente_*). O isolamento multi-tenant é feito via
filtro por departamento_id ou usuario_id do usuário autenticado quando aplicável.
"""

# ==============================================================================
# Serviço de Atendimento — EcoChatBot-MA (Refatorado)
# ==============================================================================
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import func, desc, asc, case
from sqlalchemy.orm import Session, selectinload

from app.models import Atendimento, Departamento, Usuario
from app.schemas.atendimento import (
    FiltroAtendimento, AtendimentoCreate, AtendimentoUpdate,
    AtendimentoTransferir, AtendimentoFinalizar, AtendimentoIndicadores,
)
from app.exceptions import (
    AtendimentoNaoEncontradoError,
    AtendimentoFinalizadoError,
    RecursoInvalidoError,
)


class AtendimentoService:
    def __init__(self, db: Session):
        self.db = db

    def _get_base_query(self, usuario_id: Optional[int] = None):
        """
        Query base com filtro de isolamento multi-tenant.
        Garante que o usuário só interaja com atendimentos do seu departamento.
        """
        query = self.db.query(Atendimento).filter(Atendimento.ativo == True)
        
        if usuario_id is not None:
            usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
            if usuario and usuario.departamento_id:
                query = query.filter(Atendimento.departamento_id == usuario.departamento_id)
                
        return query

    def _apply_filters(self, query, filtros: FiltroAtendimento):
        """Aplica filtros dinâmicos à query, tratando Enums com segurança."""
        if filtros.id: 
            query = query.filter(Atendimento.id == filtros.id)
        if filtros.status: 
            val = filtros.status.value if hasattr(filtros.status, 'value') else filtros.status
            query = query.filter(Atendimento.status == val)
        if filtros.tipo_canal is not None: 
            val = filtros.tipo_canal.value if hasattr(filtros.tipo_canal, 'value') else filtros.tipo_canal
            query = query.filter(Atendimento.tipo_canal == val)
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
            # +1 dia para incluir todo o dia final (até 23:59:59)
            query = query.filter(Atendimento.criado_em < filtros.data_fim + timedelta(days=1))
        if filtros.ativo is not None: 
            query = query.filter(Atendimento.ativo == filtros.ativo)
        return query

    @staticmethod
    def _gerar_protocolo() -> str:
        # Python 3.12+ compliant: timezone-aware datetime
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d')
        uid = uuid.uuid4().hex[:8].upper()
        return f"ECO-{timestamp}-{uid}"

    # ==========================================================================
    # MÉTODOS SÍNCRONOS (SEM 'async')
    # O FastAPI executa estes métodos em um threadpool, evitando bloqueio do event loop.
    # ==========================================================================

    def listar(self, filtros: Optional[FiltroAtendimento] = None, page: int = 1, limit: int = 50, order: str = "desc", usuario_id: Optional[int] = None) -> Dict[str, Any]:
        filtros = filtros or FiltroAtendimento()
        limit = min(limit, 100) # Proteção contra paginação maliciosa
        offset = (page - 1) * limit
        
        query = self._get_base_query(usuario_id)
        query = self._apply_filters(query, filtros)
        
        # OTIMIZAÇÃO: Previne o problema N+1 ao carregar relacionamentos usados na resposta
        query = query.options(
            selectinload(Atendimento.departamento),
            selectinload(Atendimento.usuario)
        )
        
        total = query.count()
        order_by = desc(Atendimento.criado_em) if order == "desc" else asc(Atendimento.criado_em)
        registros = query.order_by(order_by).offset(offset).limit(limit).all()
        
        return {
            "total": total, 
            "pagina": page, 
            "limit": limit, 
            "paginas": (total + limit - 1) // limit if total > 0 else 0, 
            "registros": registros
        }

    def buscar_por_id(self, atendimento_id: int, usuario_id: Optional[int] = None) -> Atendimento:
        atendimento = self._get_base_query(usuario_id).filter(Atendimento.id == atendimento_id).first()
        if not atendimento: 
            raise AtendimentoNaoEncontradoError(f"Atendimento {atendimento_id} não encontrado.")
        return atendimento

    def criar(self, data: AtendimentoCreate) -> Atendimento:
        if data.departamento_id:
            depto = self.db.query(Departamento).filter(
                Departamento.id == data.departamento_id, 
                Departamento.ativo == True
            ).first()
            if not depto:
                raise RecursoInvalidoError("Departamento de destino não encontrado ou inativo.")

        # Mapeamento explícito conforme arquitetura real do EcoChatBot-MA
        atendimento = Atendimento(
            protocolo=self._gerar_protocolo(), 
            telefone=data.paciente_telefone,  # Mapeamento do schema para o model
            nome_contato=data.paciente_nome,  # Mapeamento do schema para o model
            tipo_canal=data.tipo_canal.value if hasattr(data.tipo_canal, 'value') else data.tipo_canal,
            canal_id=data.canal_id, 
            departamento_id=data.departamento_id, 
            status="aberto", 
            ativo=True, 
            criado_em=datetime.now(timezone.utc)
        )
        self.db.add(atendimento)
        self.db.commit()
        self.db.refresh(atendimento)
        return atendimento

    def atualizar(self, atendimento_id: int, data: AtendimentoUpdate, usuario_id: Optional[int] = None) -> Atendimento:
        atendimento = self.buscar_por_id(atendimento_id, usuario_id)
        if atendimento.status == "finalizado": 
            raise AtendimentoFinalizadoError(f"Atendimento {atendimento_id} já está finalizado.")
            
        for key, value in data.model_dump(exclude_unset=True).items():
            if hasattr(atendimento, key): 
                setattr(atendimento, key, value)
                
        atendimento.atualizado_em = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(atendimento)
        return atendimento

    def transferir(self, atendimento_id: int, data: AtendimentoTransferir, usuario_id: int) -> Atendimento:
        atendimento = self.buscar_por_id(atendimento_id, usuario_id)
        if atendimento.status == "finalizado": 
            raise AtendimentoFinalizadoError(f"Atendimento {atendimento_id} já está finalizado.")
            
        if data.departamento_id is not None:
            if not self.db.query(Departamento).filter(Departamento.id == data.departamento_id, Departamento.ativo == True).first(): 
                raise RecursoInvalidoError("Departamento de destino não encontrado ou inativo.")
            atendimento.departamento_id = data.departamento_id
            
        if data.usuario_id is not None:
            if not self.db.query(Usuario).filter(Usuario.id == data.usuario_id, Usuario.ativo == True).first(): 
                raise RecursoInvalidoError("Usuário de destino não encontrado ou inativo.")
            atendimento.usuario_id = data.usuario_id
            
        if data.canal_id is not None: 
            atendimento.canal_id = data.canal_id
            
        # Regra de negócio: se tem usuário atribuído, status é "em_atendimento", senão "fila"
        atendimento.status = "em_atendimento" if atendimento.usuario_id else "fila"
        atendimento.atualizado_em = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(atendimento)
        return atendimento

    def finalizar(self, atendimento_id: int, data: Optional[AtendimentoFinalizar] = None, usuario_id: Optional[int] = None) -> Atendimento:
        atendimento = self.buscar_por_id(atendimento_id, usuario_id)
        if atendimento.status == "finalizado": 
            raise AtendimentoFinalizadoError(f"Atendimento {atendimento_id} já está finalizado.")
            
        atendimento.status = "finalizado"
        atendimento.atualizado_em = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(atendimento)
        return atendimento

    def indicadores(self, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None, usuario_id: Optional[int] = None) -> AtendimentoIndicadores:
        """
        OTIMIZAÇÃO CRÍTICA DE DESEMPENHO:
        Substitui múltiplas chamadas .count() sequenciais por agregação condicional (GROUP BY / CASE).
        Reduz o tempo de resposta de O(N) consultas para O(1), escalável para milhões de registros.
        """
        query = self._get_base_query(usuario_id)
        if data_inicio: 
            query = query.filter(Atendimento.criado_em >= data_inicio)
        if data_fim: 
            query = query.filter(Atendimento.criado_em < data_fim + timedelta(days=1))

        # 1. Contagens por status em UMA ÚNICA consulta (GROUP BY)
        status_counts = query.with_entities(
            Atendimento.status, func.count(Atendimento.id).label('qtd')
        ).group_by(Atendimento.status).all()
        
        counts_dict = {row.status: row.qtd for row in status_counts}
        
        total = sum(counts_dict.values())
        aberto = counts_dict.get("aberto", 0)
        fila = counts_dict.get("fila", 0)
        em_atendimento = counts_dict.get("em_atendimento", 0)
        
        # 2. Finalizados separados por atendimento humano vs. sem atendente (CASE WHEN)
        finalizados_detail = query.filter(Atendimento.status == "finalizado").with_entities(
            func.count(case((Atendimento.usuario_id.isnot(None), 1))).label('com_atendente'),
            func.count(case((Atendimento.usuario_id.is_(None), 1))).label('sem_atendente')
        ).first()
        
        finalizado_humano = finalizados_detail.com_atendente if finalizados_detail else 0
        finalizado_sem_atendente = finalizados_detail.sem_atendente if finalizados_detail else 0
        
        # 3. Dados por departamento (JOIN otimizado)
        dept_rows = query.outerjoin(Departamento, Atendimento.departamento_id == Departamento.id).with_entities(
            Atendimento.departamento_id, 
            func.coalesce(Departamento.nome, "Sem Departamento").label("nome"), 
            func.count(Atendimento.id).label("total")
        ).group_by(Atendimento.departamento_id, Departamento.nome).all()
        
        finalizados_por_depto_query = query.filter(Atendimento.status == "finalizado").with_entities(
            Atendimento.departamento_id, func.count(Atendimento.id).label('qtd')
        ).group_by(Atendimento.departamento_id).all()
        finalizados_por_depto = {row.departamento_id: row.qtd for row in finalizados_por_depto_query}
        
        por_departamento = [
            {
                "departamento_id": d_id, 
                "nome": n, 
                "total": t, 
                "finalizados": finalizados_por_depto.get(d_id, 0), 
                "em_aberto": t - finalizados_por_depto.get(d_id, 0)
            } 
            for d_id, n, t in dept_rows if d_id is not None or n == "Sem Departamento"
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
            tempo_medio_atendimento=None
        )