# ==============================================================================
# Arquivo: contato_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Agenda de clientes WhatsApp ("Contatos" na sidebar, ver docs/Barra Menu.png).
# Serve como base de destinatários para o disparo de Campanhas.
# ==============================================================================

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Contato
from app.schemas import ContatoCreate, ContatoUpdate


class ContatoService:

    @staticmethod
    def listar(db: Session) -> List[Contato]:
        return db.query(Contato).order_by(Contato.nome).all()

    @staticmethod
    def buscar_por_id(db: Session, contato_id: int) -> Optional[Contato]:
        return db.query(Contato).filter(Contato.id == contato_id).first()

    @staticmethod
    def criar(db: Session, dto: ContatoCreate) -> Contato:
        db_contato = Contato(
            nome=dto.nome,
            telefone=dto.telefone,
            email=dto.email,
            empresa=dto.empresa,
            observacao=dto.observacao,
            ativo=dto.ativo,
            origem="manual",
        )
        db.add(db_contato)
        db.commit()
        db.refresh(db_contato)
        return db_contato

    @staticmethod
    def atualizar(db: Session, contato_id: int, dto: ContatoUpdate) -> Optional[Contato]:
        db_contato = db.query(Contato).filter(Contato.id == contato_id).first()
        if not db_contato:
            return None

        for campo, valor in dto.model_dump(exclude_unset=True).items():
            setattr(db_contato, campo, valor)

        db.commit()
        db.refresh(db_contato)
        return db_contato

    @staticmethod
    def deletar(db: Session, contato_id: int) -> bool:
        db_contato = db.query(Contato).filter(Contato.id == contato_id).first()
        if not db_contato:
            return False

        db.delete(db_contato)
        db.commit()
        return True
