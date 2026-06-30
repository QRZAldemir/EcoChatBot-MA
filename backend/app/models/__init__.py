from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Atendimento(Base):
    __tablename__ = "atendimentos"

    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String(50), unique=True, index=True)
    telefone = Column(String(20), nullable=False)
    nome_contato = Column(String(100))
    cliente_id = Column(Integer, index=True)
    canal = Column(Integer, default=1)           # 1=WhatsApp, 2=Interno
    canal_id = Column(Integer, ForeignKey("canais.id"))
    conexao_id = Column(Integer, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    tipo = Column(Integer, default=1)            # 1=automático, 2=manual
    ativo = Column(Boolean, default=True)
    status = Column(String(30), default="aberto")  # aberto, em_atendimento, finalizado
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    canal = relationship("Canal")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    departamento = relationship("Departamento")
    contextos = relationship("AtendimentoContext", back_populates="atendimento", cascade="all, delete-orphan")


class AtendimentoContext(Base):
    __tablename__ = "atendimento_contextos"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=False)
    context_key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    atendimento = relationship("Atendimento", back_populates="contextos")


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
    arquivo_menu = Column(String(200), nullable=False)  # Ex: 7portaria-ma.html
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    departamento = relationship("Departamento", back_populates="canais")
    usuarios = relationship("Usuario", back_populates="canal")
    menus = relationship("Menu", back_populates="canal")

class MenuOpcao(Base):
    __tablename__ = "menu_opcoes"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String(300))
    row_id = Column(String(50), nullable=False)
    ordem = Column(Integer, default=0)

    menu = relationship("Menu", back_populates="opcoes")


class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String(300))
    rodape = Column(String(100))
    texto_botao = Column(String(50), default="Ver opções")
    canal_id = Column(Integer, ForeignKey("canais.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    opcoes = relationship("MenuOpcao", back_populates="menu", order_by="MenuOpcao.ordem")
    canal = relationship("Canal", back_populates="menus")


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
