from sqlalchemy.orm import Session
from app.models import ModeloMensagem
from app.schemas import ModeloMensagemCreate, ModeloMensagemUpdate
from typing import List, Optional


class ModeloMensagemService:

    @staticmethod
    def listar(db: Session, departamento_id: Optional[int] = None, apenas_ativos: bool = False) -> List[ModeloMensagem]:
        query = db.query(ModeloMensagem)
        if departamento_id:
            query = query.filter(ModeloMensagem.departamento_id == departamento_id)
        if apenas_ativos:
            query = query.filter(ModeloMensagem.ativo == True)
        return query.order_by(ModeloMensagem.criado_em.desc()).all()

    @staticmethod
    def buscar_por_id(db: Session, modelo_id: int) -> Optional[ModeloMensagem]:
        return db.query(ModeloMensagem).filter(ModeloMensagem.id == modelo_id).first()

    @staticmethod
    def criar(db: Session, modelo: ModeloMensagemCreate) -> ModeloMensagem:
        db_modelo = ModeloMensagem(
            descricao=modelo.descricao,
            corpo=modelo.corpo,
            arquivo=modelo.arquivo,
            departamento_id=modelo.departamento_id,
            ativo=modelo.ativo,
        )
        db.add(db_modelo)
        db.commit()
        db.refresh(db_modelo)
        return db_modelo

    @staticmethod
    def atualizar(db: Session, modelo_id: int, modelo: ModeloMensagemUpdate) -> Optional[ModeloMensagem]:
        db_modelo = db.query(ModeloMensagem).filter(ModeloMensagem.id == modelo_id).first()
        if not db_modelo:
            return None
        for campo, valor in modelo.model_dump(exclude_unset=True).items():
            setattr(db_modelo, campo, valor)
        db.commit()
        db.refresh(db_modelo)
        return db_modelo

    @staticmethod
    def deletar(db: Session, modelo_id: int) -> bool:
        db_modelo = db.query(ModeloMensagem).filter(ModeloMensagem.id == modelo_id).first()
        if not db_modelo:
            return False
        db.delete(db_modelo)
        db.commit()
        return True
