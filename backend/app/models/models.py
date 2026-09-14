"""
================================================================================
MÓDULO: app/models.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.0 (Definição inicial dos modelos de domínio com SQLAlchemy)

DESCRIÇÃO:
    Define as tabelas e relacionamentos do banco de dados utilizando o ORM 
    do SQLAlchemy. Este arquivo atua como a "fonte da verdade" para a estrutura 
    de dados da aplicação, garantindo integridade referencial através de 
    Foreign Keys e facilitando as consultas via objetos Python.

CONTEXTO ARQUITETURAL:
    - Banco de Dados: PostgreSQL
    - ORM: SQLAlchemy 2.x
    - Padrão: Declarative Base (importado de app.database)

PÚBLICO-ALVO DA DOCUMENTAÇÃO:
    Desenvolvedores da equipe que precisam entender a estrutura de dados, 
    adicionar novos campos ou criar novas relações entre as entidades do sistema.
================================================================================
Pontos de Atenção e Melhorias Aplicadas:
Integridade Referencial (ondelete="CASCADE"):
Nas Foreign Keys de Usuario e InstanciaChatbot, adicionei a cláusula ondelete="CASCADE". Isso garante que, se uma Empresa for removida do sistema, todos os seus usuários e instâncias associados sejam automaticamente limpos pelo PostgreSQL, evitando órfãos de dados e inconsistências.
Bidirecionalidade (back_populates):
A propriedade back_populates foi espelhada corretamente em ambos os lados da relação. Isso permite que, ao carregar um objeto Empresa, o SQLAlchemy possa acessar empresa.usuarios ou empresa.instancias diretamente, sem a necessidade de consultas manuais adicionais.
Comentários no Banco de Dados (comment=...):
Utilizei o parâmetro comment nas colunas. Ao executar as migrações (Alembic), esses comentários serão refletidos diretamente no schema do PostgreSQL, servindo como um dicionário de dados vivo e acessível para qualquer administrador de banco de dados que inspecione as tabelas.
Prevenção de Órfãos (cascade="all, delete-orphan"):
No relacionamento da Empresa, adicionei a política de cascata. Isso reforça a limpeza automática no nível do ORM do SQLAlchemy, alinhando-se à regra de cascata do banco de dados.
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

# Importa a Base declarativa configurada no módulo de banco de dados
from app.database import Base


# ==============================================================================
# MODELO: Empresa
# ==============================================================================
class Empresa(Base):
    """
    Representa uma organização cliente que utiliza a plataforma de chatbot.
    Atua como a entidade raiz para isolamento de dados (multi-tenancy lógico).
    """
    __tablename__ = "empresas"

    # Colunas
    id = Column(BigInteger, primary_key=True, index=True, comment="Identificador único da empresa")
    nome = Column(String(255), nullable=False, comment="Nome fantasia ou razão social da empresa")
    cnpj_cpf = Column(String(20), unique=True, index=True, nullable=True, comment="CNPJ ou CPF para fins fiscais e identificação única")
    email_contato = Column(String(255), nullable=False, comment="E-mail principal para notificações e recuperação de acesso")
    telefone = Column(String(30), nullable=True, comment="Telefone de contato comercial ou suporte")
    
    plano = Column(String(50), default="starter", comment="Nível do plano contratado (ex: starter, pro, enterprise)")
    max_instancias = Column(BigInteger, default=1, comment="Limite de instâncias de chatbot permitidas para esta empresa")
    
    ativo = Column(Boolean, default=True, comment="Indica se a empresa está ativa e pode utilizar os serviços")
    
    # Timestamps de auditoria
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data e hora de criação do registro")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Data e hora da última modificação")

    # Relacionamentos (Back-populates garantem a bidirecionalidade)
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    instancias = relationship("InstanciaChatbot", back_populates="empresa", cascade="all, delete-orphan")


# ==============================================================================
# MODELO: Usuario
# ==============================================================================
class Usuario(Base):
    """
    Representa um usuário humano (administrador, atendente ou gestor) 
    vinculado a uma empresa específica.
    """
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True)
    
    # Foreign Key: Vincula este usuário a uma empresa existente
    empresa_id = Column(BigInteger, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True, comment="Referência à empresa à qual o usuário pertence")
    
    nome = Column(String(255), nullable=False, comment="Nome completo do usuário")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="E-mail único para login e autenticação")
    senha_hash = Column(String(255), nullable=False, comment="Hash da senha (nunca armazenar senha em texto puro)")
    perfil = Column(String(50), default="atendente", comment="Nível de permissão (ex: admin, gestor, atendente)")
    
    ativo = Column(Boolean, default=True, comment="Indica se o usuário pode acessar o sistema")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento bidirecional com Empresa
    empresa = relationship("Empresa", back_populates="usuarios")


# ==============================================================================
# MODELO: InstanciaChatbot
# ==============================================================================
class InstanciaChatbot(Base):
    """
    Representa uma instância de conexão com a Evolution API (WhatsApp) 
    pertencente a uma empresa específica.
    """
    __tablename__ = "instancias_chatbot"

    id = Column(BigInteger, primary_key=True, index=True)
    
    # Foreign Key: Vincula esta instância a uma empresa existente
    empresa_id = Column(BigInteger, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True, comment="Referência à empresa proprietária desta instância")
    
    nome_instancia = Column(String(100), unique=True, index=True, nullable=False, comment="Nome identificador da instância na Evolution API (ex: 'empresa_x_suporte')")
    numero_whatsapp = Column(String(30), unique=True, nullable=True, comment="Número de telefone vinculado ao QR Code pareado")
    
    status_conexao = Column(String(50), default="desconectado", comment="Estado atual da conexão (ex: conectando, aberto, desconectado)")
    webhook_url = Column(Text, nullable=True, comment="URL de callback configurada na Evolution API para esta instância")
    
    ativo = Column(Boolean, default=True, comment="Indica se a instância está habilitada para receber/enviar mensagens")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento bidirecional com Empresa
    empresa = relationship("Empresa", back_populates="instancias")