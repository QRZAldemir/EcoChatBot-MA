from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class NivelUsuario(Base):
    __tablename__ = "nivel_usuario"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True, nullable=False)  # atendente, supervisor, gerente, administrador
    descricao = Column(String(200))
    
    # Relacionamento com usuários
    usuarios = relationship("Usuario", back_populates="nivel")

class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(300))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="departamento")
    canais = relationship("Canal", back_populates="departamento")

class Canal(Base):
    __tablename__ = "canais"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(300))
    arquivo_menu = Column(String(200), nullable=False)  # Ex: 7portaria-mackenzie.html
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    departamento = relationship("Departamento", back_populates="canais")
    usuarios = relationship("Usuario", back_populates="canal")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20))
    
    nivel_id = Column(Integer, ForeignKey("nivel_usuario.id"), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    canal_id = Column(Integer, ForeignKey("canais.id"))
    
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    nivel = relationship("NivelUsuario", back_populates="usuarios")
    departamento = relationship("Departamento", back_populates="usuarios")
    canal = relationship("Canal", back_populates="usuarios")
