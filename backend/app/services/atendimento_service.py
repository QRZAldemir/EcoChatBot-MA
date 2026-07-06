from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from app.models import Atendimento, AtendimentoContext
from typing import Optional, List
from datetime import datetime


class AtendimentoService:

    @staticmethod
    def listar(
        db: Session,
        id: Optional[int] = None,
        canal: Optional[int] = None,
        ativo: Optional[str] = None,
        data_criacao_inicio: Optional[str] = None,
        data_criacao_fim: Optional[str] = None,
        tipo: Optional[int] = None,
        departamento_id: Optional[int] = None,
        atendente_usuario_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        protocolo: Optional[str] = None,
        conexao_id: Optional[int] = None,
        limit: int = 10,
        page: int = 1,
        order: str = "desc",
    ) -> dict:
        limit = min(limit, 50)
        offset = (page - 1) * limit

        query = db.query(Atendimento)

        if id:
            query = query.filter(Atendimento.id == id)
        if canal:
            query = query.filter(Atendimento.canal == canal)
        if ativo is not None:
            query = query.filter(Atendimento.ativo == (ativo.upper() == "S"))
        if tipo:
            query = query.filter(Atendimento.tipo == tipo)
        if departamento_id:
            query = query.filter(Atendimento.departamento_id == departamento_id)
        if atendente_usuario_id:
            query = query.filter(Atendimento.usuario_id == atendente_usuario_id)
        if cliente_id:
            query = query.filter(Atendimento.cliente_id == cliente_id)
        if protocolo:
            query = query.filter(Atendimento.protocolo == protocolo)
        if conexao_id:
            query = query.filter(Atendimento.conexao_id == conexao_id)
        if data_criacao_inicio:
            query = query.filter(Atendimento.criado_em >= datetime.fromisoformat(data_criacao_inicio))
        if data_criacao_fim:
            query = query.filter(Atendimento.criado_em <= datetime.fromisoformat(data_criacao_fim + "T23:59:59"))

        total = query.count()
        ordenar = desc(Atendimento.criado_em) if order == "desc" else asc(Atendimento.criado_em)
        registros = query.order_by(ordenar).offset(offset).limit(limit).all()

        return {
            "total": total,
            "pagina": page,
            "limit": limit,
            "paginas": (total + limit - 1) // limit,
            "registros": registros,
        }

    @staticmethod
    def buscar_por_id(db: Session, atendimento_id: int) -> Optional[Atendimento]:
        return db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()

    @staticmethod
    def transferir(
        db: Session,
        atendimento_id: int,
        departamento_id: Optional[int] = None,
        atendente_usuario_id: Optional[int] = None,
        canal_id: Optional[int] = None,
    ) -> Optional[Atendimento]:
        """
        Transfere o atendimento para outro departamento/atendente/canal.

        canal_id precisa ser passado explicitamente (e não apenas inferido de
        departamento_id) porque um departamento pode ter mais de um canal —
        quem chama decide qual canal real herda a conversa. Sem atualizar
        canal_id, o atendimento continuaria preso ao canal antigo para o
        resto do sistema (bot_service, notificações etc.), mesmo após trocar
        de departamento.
        """
        atendimento = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
        if not atendimento:
            return None
        if departamento_id is not None:
            atendimento.departamento_id = departamento_id
        if atendente_usuario_id is not None:
            atendimento.usuario_id = atendente_usuario_id
        if canal_id is not None:
            atendimento.canal_id = canal_id
        atendimento.status = "em_atendimento"
        db.commit()
        db.refresh(atendimento)
        return atendimento

    @staticmethod
    def encerrar(db: Session, atendimento_id: int) -> Optional[Atendimento]:
        atendimento = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
        if not atendimento:
            return None
        atendimento.status = "finalizado"
        db.commit()
        db.refresh(atendimento)
        return atendimento

    @staticmethod
    def buscar_context(db: Session, atendimento_id: int, context_key: str) -> Optional[AtendimentoContext]:
        return (
            db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == context_key,
            )
            .first()
        )

    @staticmethod
    def deletar_context(db: Session, atendimento_id: int, context_key: str) -> bool:
        ctx = (
            db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == context_key,
            )
            .first()
        )
        if not ctx:
            return False
        db.delete(ctx)
        db.commit()
        return True

    @staticmethod
    def criar_altera_context(
        db: Session,
        atendimento_id: int,
        context_key: str,
        value: str,
    ) -> Optional[AtendimentoContext]:
        if not db.query(Atendimento).filter(Atendimento.id == atendimento_id).first():
            return None

        ctx = (
            db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == context_key,
            )
            .first()
        )

        if ctx:
            ctx.value = value
        else:
            ctx = AtendimentoContext(
                atendimento_id=atendimento_id,
                context_key=context_key,
                value=value,
            )
            db.add(ctx)

        db.commit()
        db.refresh(ctx)
        return ctx
