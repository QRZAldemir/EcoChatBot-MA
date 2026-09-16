# tests/conftest.py
"""
Configuração central de fixtures para a suíte de testes do EcoChatBot-MA.
Utiliza SQLite em memória para velocidade e isolamento entre testes.
"""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import Atendimento, Departamento, Usuario, Canal
from app.services.atendimento_service import AtendimentoService


# ==============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS DE TESTE
# ==============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário para SQLite com threads
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==============================================================================
# FIXTURES DE BANCO DE DADOS
# ==============================================================================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Fixture que fornece uma sessão de banco de dados limpa para cada teste.
    Cria todas as tabelas antes do teste e as remove após a execução.
    """
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Fixture que cria um cliente de teste do FastAPI com injeção de dependência
    do banco de dados de teste.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def service(db_session: Session) -> AtendimentoService:
    """
    Fixture que fornece uma instância do AtendimentoService com a sessão de teste.
    """
    return AtendimentoService(db_session)


# ==============================================================================
# FIXTURES DE DADOS DE TESTE
# ==============================================================================

@pytest.fixture
def canal_whatsapp(db_session: Session) -> Canal:
    """Cria um canal de WhatsApp de teste."""
    canal = Canal(
        nome="WhatsApp Principal",
        tipo=1,  # WhatsApp
        ativo=True
    )
    db_session.add(canal)
    db_session.commit()
    db_session.refresh(canal)
    return canal


@pytest.fixture
def departamento_triagem(db_session: Session) -> Departamento:
    """Cria um departamento de Triagem."""
    depto = Departamento(
        nome="Triagem",
        ativo=True
    )
    db_session.add(depto)
    db_session.commit()
    db_session.refresh(depto)
    return depto


@pytest.fixture
def departamento_suporte(db_session: Session) -> Departamento:
    """Cria um departamento de Suporte."""
    depto = Departamento(
        nome="Suporte Técnico",
        ativo=True
    )
    db_session.add(depto)
    db_session.commit()
    db_session.refresh(depto)
    return depto


@pytest.fixture
def usuario_atendente(db_session: Session, departamento_triagem: Departamento) -> Usuario:
    """Cria um usuário atendente vinculado ao departamento de Triagem."""
    usuario = Usuario(
        nome="João Atendente",
        email="joao@ecochatbot.com",
        departamento_id=departamento_triagem.id,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture
def usuario_suporte(db_session: Session, departamento_suporte: Departamento) -> Usuario:
    """Cria um usuário atendente vinculado ao departamento de Suporte."""
    usuario = Usuario(
        nome="Maria Suporte",
        email="maria@ecochatbot.com",
        departamento_id=departamento_suporte.id,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture
def atendimento_aberto(
    db_session: Session,
    departamento_triagem: Departamento,
    canal_whatsapp: Canal
) -> Atendimento:
    """Cria um atendimento em status 'aberto'."""
    atendimento = Atendimento(
        protocolo="ECO-TESTE-001",
        telefone="5511999999999",
        nome_contato="Paciente Teste",
        tipo_canal=1,  # WhatsApp
        canal_id=canal_whatsapp.id,
        departamento_id=departamento_triagem.id,
        usuario_id=None,  # Sem atendente atribuído
        status="aberto",
        ativo=True,
        criado_em=datetime.now(timezone.utc)
    )
    db_session.add(atendimento)
    db_session.commit()
    db_session.refresh(atendimento)
    return atendimento


@pytest.fixture
def atendimento_em_fila(
    db_session: Session,
    departamento_triagem: Departamento,
    canal_whatsapp: Canal
) -> Atendimento:
    """Cria um atendimento em status 'fila'."""
    atendimento = Atendimento(
        protocolo="ECO-TESTE-002",
        telefone="5511888888888",
        nome_contato="Paciente Fila",
        tipo_canal=1,
        canal_id=canal_whatsapp.id,
        departamento_id=departamento_triagem.id,
        usuario_id=None,
        status="fila",
        ativo=True,
        criado_em=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(atendimento)
    db_session.commit()
    db_session.refresh(atendimento)
    return atendimento


@pytest.fixture
def atendimento_em_atendimento(
    db_session: Session,
    departamento_triagem: Departamento,
    usuario_atendente: Usuario,
    canal_whatsapp: Canal
) -> Atendimento:
    """Cria um atendimento em status 'em_atendimento' com atendente atribuído."""
    atendimento = Atendimento(
        protocolo="ECO-TESTE-003",
        telefone="5511777777777",
        nome_contato="Paciente em Atendimento",
        tipo_canal=1,
        canal_id=canal_whatsapp.id,
        departamento_id=departamento_triagem.id,
        usuario_id=usuario_atendente.id,
        status="em_atendimento",
        ativo=True,
        criado_em=datetime.now(timezone.utc) - timedelta(hours