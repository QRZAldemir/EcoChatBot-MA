"""
Fixtures da suíte do EcoChatBot-MA.

BANCO DE TESTE
--------------
SQLite **assíncrono** (`sqlite+aiosqlite`). O serviço é todo `async def` e
depende de `AsyncSession`; um `Session` síncrono não exercita o mesmo caminho de
código do que a aplicação real, então o teste passaria sem provar nada.

`StaticPool` é obrigatório: sem ele, cada conexão abriria um banco em memória
NOVO e vazio, e o `create_all` de uma conexão não apareceria na outra.

GRAFO DE TENANT
---------------
Os testes montam a cadeia real, porque as regras de negócio dependem dela:

    Cliente  →  Empresa  →  Telefone  →  CanalContratado

`Empresa` é o tenant. `Cliente` é a conta comercial (plano, limites) e fica
ACIMA do tenant. Um canal só existe apoiado em um telefone, e o telefone
pertence a uma empresa — é esse elo que impede um tenant de contratar canal
sobre o número de outro.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Importar o pacote registra as 30 tabelas no Base.metadata. Sem esta linha o
# create_all cria um banco vazio e todo teste falha com "no such table".
import app.models  # noqa: F401
from app.models.base import Base
from app.models import Cliente, Empresa, Telefone

TEST_DATABASE_URL = "sqlite+aiosqlite://"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# BANCO
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def engine() -> AsyncGenerator:
    eng = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Sessão assíncrona limpa por teste."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ══════════════════════════════════════════════════════════════════════════════
# TENANT
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def cliente(db_session: AsyncSession) -> Cliente:
    """Conta comercial. NÃO é o tenant."""
    c = Cliente(
        razao_social="Clínica Exemplo LTDA",
        nome_fantasia="Clínica Exemplo",
        cnpj="11222333000181",
        slug="clinica-exemplo",
        email="contato@clinicaexemplo.com.br",
        plano="profissional",
        limite_empresas=5,
        limite_usuarios=50,
        limite_canais=10,
        ativo=True,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest_asyncio.fixture
async def empresa(db_session: AsyncSession, cliente: Cliente) -> Empresa:
    """Tenant principal."""
    e = Empresa(
        razao_social="Clínica Exemplo Unidade Centro",
        nome_fantasia="Clínica Centro",
        slug="clinica-centro",
        cnpj="11222333000181",
        email="centro@clinicaexemplo.com.br",
        cliente_id=cliente.id,
        ativo=True,
    )
    db_session.add(e)
    await db_session.commit()
    await db_session.refresh(e)
    return e


@pytest_asyncio.fixture
async def outra_empresa(db_session: AsyncSession, cliente: Cliente) -> Empresa:
    """SEGUNDO tenant do mesmo cliente.

    Existe para provar isolamento: como as duas estão sob o mesmo `Cliente`, um
    filtro por `cliente_id` deixaria uma ver a outra. O isolamento real é por
    `Empresa`.
    """
    e = Empresa(
        razao_social="Clínica Exemplo Unidade Norte",
        nome_fantasia="Clínica Norte",
        slug="clinica-norte",
        cnpj="11222333000182",
        email="norte@clinicaexemplo.com.br",
        cliente_id=cliente.id,
        ativo=True,
    )
    db_session.add(e)
    await db_session.commit()
    await db_session.refresh(e)
    return e


# ══════════════════════════════════════════════════════════════════════════════
# TELEFONE
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def telefone(db_session: AsyncSession, empresa: Empresa) -> Telefone:
    t = Telefone(
        numero="5511988880001",
        pais="BR",
        descricao="WhatsApp comercial",
        principal=True,
        ativo=True,
        empresa_id=empresa.id,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def telefone_outra_empresa(
    db_session: AsyncSession, outra_empresa: Empresa
) -> Telefone:
    t = Telefone(
        numero="5511988880002",
        pais="BR",
        descricao="WhatsApp da unidade norte",
        principal=True,
        ativo=True,
        empresa_id=outra_empresa.id,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def telefone_inativo(db_session: AsyncSession, empresa: Empresa) -> Telefone:
    t = Telefone(
        numero="5511988880003",
        pais="BR",
        descricao="Número desligado",
        principal=False,
        ativo=False,
        empresa_id=empresa.id,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ══════════════════════════════════════════════════════════════════════════════
# CONTATO
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def contato(db_session: AsyncSession, empresa: Empresa):
    """Pessoa do outro lado do canal.

    `Atendimento.contato_id` é NOT NULL: um atendimento sem contato não sabe
    com quem está falando, e o histórico perde o interlocutor.
    """
    from app.models import Contato

    c = Contato(
        nome="Maria Souza",
        canal_tipo="whatsapp",
        canal_identificador="5511988880001",
        telefone="5511988880001",
        empresa_id=empresa.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


# ══════════════════════════════════════════════════════════════════════════════
# TRANSPARENCIA DA SUITE
# ══════════════════════════════════════════════════════════════════════════════
#
# Arquivos em `_quarentena/` nao sao coletados. Eles nao estao "passando": sao
# testes que NAO rodam. Este cabecalho e impresso a cada execucao para que um
# `pytest` verde nunca seja lido como cobertura completa.
collect_ignore_glob = ["_quarentena/*"]


def pytest_report_header(config):
    import pathlib

    pasta = pathlib.Path(__file__).resolve().parents[2] / "_quarentena"
    arquivos = sorted(p.name for p in pasta.glob("*.legado")) if pasta.is_dir() else []
    if not arquivos:
        return None
    return (
        f"ATENCAO: {len(arquivos)} arquivo(s) legado(s) em _quarentena/ NAO "
        f"sao executados: {', '.join(arquivos)}\n"
        f"         Testam modulos ainda sincronos (frente C). Ver _quarentena/README.md"
    )


# ══════════════════════════════════════════════════════════════════════════════
# DEPARTAMENTO
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def departamento(db_session: AsyncSession, empresa: Empresa):
    """`MenuItem.departamento_id` é obrigatório e ON DELETE RESTRICT."""
    from app.models import Departamento

    d = Departamento(nome="Financeiro", empresa_id=empresa.id, ativo=True)
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest_asyncio.fixture
async def departamento_outra_empresa(db_session: AsyncSession, outra_empresa: Empresa):
    from app.models import Departamento

    d = Departamento(nome="Juridico", empresa_id=outra_empresa.id, ativo=True)
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d
