from sqlalchemy.orm import Session
from app.models import Departamento
from app.schemas import DepartamentoCreate, DepartamentoUpdate
from typing import List, Optional

class DepartamentoService:
    
    @staticmethod
    def listar_departamentos(db: Session) -> List[Departamento]:
        """Listar todos os departamentos"""
        return db.query(Departamento).all()
    
    @staticmethod
    def buscar_por_id(db: Session, depto_id: int) -> Optional[Departamento]:
        """Buscar departamento por ID"""
        return db.query(Departamento).filter(Departamento.id == depto_id).first()
    
    @staticmethod
    def criar_departamento(db: Session, departamento: DepartamentoCreate) -> Departamento:
        """Criar novo departamento"""
        db_departamento = Departamento(
            nome=departamento.nome,
            descricao=departamento.descricao,
            ativo=departamento.ativo
        )
        db.add(db_departamento)
        db.commit()
        db.refresh(db_departamento)
        return db_departamento
    
    @staticmethod
    def atualizar_departamento(db: Session, depto_id: int, 
                              departamento: DepartamentoUpdate) -> Optional[Departamento]:
        """Atualizar departamento existente"""
        db_departamento = db.query(Departamento).filter(Departamento.id == depto_id).first()
        if not db_departamento:
            return None
        
        update_data = departamento.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(db_departamento, campo, valor)
        
        db.commit()
        db.refresh(db_departamento)
        return db_departamento
    
    @staticmethod
    def deletar_departamento(db: Session, depto_id: int) -> bool:
        """Deletar departamento"""
        db_departamento = db.query(Departamento).filter(Departamento.id == depto_id).first()
        if not db_departamento:
            return False
        
        db.delete(db_departamento)
        db.commit()
        return True
