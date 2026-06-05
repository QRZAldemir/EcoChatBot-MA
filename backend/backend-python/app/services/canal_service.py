from sqlalchemy.orm import Session
from app.models import Canal
from app.schemas import CanalCreate, CanalUpdate
from typing import List, Optional

class CanalService:
    
    @staticmethod
    def listar_canais(db: Session) -> List[Canal]:
        """Listar todos os canais"""
        return db.query(Canal).all()
    
    @staticmethod
    def buscar_por_id(db: Session, canal_id: int) -> Optional[Canal]:
        """Buscar canal por ID"""
        return db.query(Canal).filter(Canal.id == canal_id).first()
    
    @staticmethod
    def criar_canal(db: Session, canal: CanalCreate) -> Canal:
        """Criar novo canal"""
        db_canal = Canal(
            nome=canal.nome,
            descricao=canal.descricao,
            arquivo_menu=canal.arquivo_menu,
            departamento_id=canal.departamento_id,
            ativo=canal.ativo
        )
        db.add(db_canal)
        db.commit()
        db.refresh(db_canal)
        return db_canal
    
    @staticmethod
    def atualizar_canal(db: Session, canal_id: int, 
                       canal: CanalUpdate) -> Optional[Canal]:
        """Atualizar canal existente"""
        db_canal = db.query(Canal).filter(Canal.id == canal_id).first()
        if not db_canal:
            return None
        
        update_data = canal.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(db_canal, campo, valor)
        
        db.commit()
        db.refresh(db_canal)
        return db_canal
    
    @staticmethod
    def deletar_canal(db: Session, canal_id: int) -> bool:
        """Deletar canal"""
        db_canal = db.query(Canal).filter(Canal.id == canal_id).first()
        if not db_canal:
            return False
        
        db.delete(db_canal)
        db.commit()
        return True
