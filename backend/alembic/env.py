"""
================================================================================
ALEMBIC - PONTO DE ENTRADA (environment)
================================================================================
Este arquivo e o QUE o Alembic executa em todo comando. Ele responde a tres
perguntas:

    1. Onde esta o banco?          -> config
    2. Qual e a "foto" do schema?  -> target_metadata
    3. Como executo aqui?          -> run_migrations_online / _offline

POR QUE ESTE ARQUIVO USA ENGINE ASSINCRONA
------------------------------------------
A aplicacao do EcoChatBot-MA e async-only: `app/database.py` cria
`create_async_engine` e NAO existe engine sincrona. Um env.py sincrono
padrao falharia com "NoSuchModuleError: asyncpg" ou, pior, conectaria
usando um driver diferente do que a app usa em producao - e ai a migration
seria validada contra um banco que a app nunca enxerga.

Como o Alembic exige `connection` sincrona mesmo em modo async, a ponte e
`run_sync`, que entrega a conexao no Greenlet e roda o codigo sincrono
dentro da event loop.

O QUE FAZ O AUTOGENERATE ENCONTRAR AS DIFERENCAS
------------------------------------------------
O Alembic so enxerga as tabelas que foram IMPORTADAS quando o `Base` foi
criado. Se um model existe no arquivo mas nao foi importado, ele e
invisivel para o autogenerate: o Alembic diria "esta tudo em dia" e geraria
uma migration vazia. Por isso o bloco `import app.models` abaixo e
OBRIGATORIO e nao decorativo.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Configuracao de logging do arquivo .ini ───────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── O schema "oficial" da aplicacao ───────────────────────────────────────────
from app.models.base import Base  # noqa: E402

# Sem estes imports, o Base.metadata vem pela metade e o autogenerate acha
# que o banco esta em dia. Commentado de proposito: basta descomentar
# quando criar um model novo, para o teste nao passar em branco.
import app.models  # noqa: E402,F401

target_metadata = Base.metadata


# ── 1. ONDE ESTA O BANCO ──────────────────────────────────────────────────────
def _url_assincrona() -> str:
    """
    URL async vinda do `.env`, via app/config.py.

    Nao leemos `config.get_main_option("sqlalchemy.url")` de proposito: o
    `.ini` fica com o campo vazio para a senha nunca entrar no Git. O .env
    e o unico lugar que tem credencial, e o .env ja esta no .gitignore.
    """
    from app.config import settings

    return settings.async_database_url


def _url_sincrona() -> str:
    """
    Mesma URL, com driver sincrono.

    Usada so no modo offline (`alembic upgrade head --sql`), em que o
    Alembic apenas imprime o SQL e nao abre conexao. `psycopg2` e o driver
    sincrono que o projeto ja declara em requirements.txt.
    """
    from app.config import settings

    return settings.async_database_url.replace("+asyncpg", "+psycopg2")


# ── 2. COMO COMPARAR E GERAR O DIFF ───────────────────────────────────────────
def _filtro_de_tabela(nome: str, tipo: str, *_args) -> bool:
    """
    Decide se o autogenerate deve tocar numa tabela.

    Duas exclusoes:

    - `alembic_version`: e o controle do proprio Alembic. Gerar migration
      para ele seria circular.

    - `tokens_revogados`: o cleanup e feito por rotina periodica, e o
      Alembic mexer aqui briga com o `alembic/expiration.py` se existir.
      Se um dia precisar, e so remover a linha.
    """
    return nome not in {"alembic_version", "tokens_revogados"}


def run_migrations_offline() -> None:
    """
    Modo offline: NAO conecta no banco, so imprime o SQL.

    Serve para revisar a migration antes de aplicar, ou para rodar num
    pipeline que aplica o SQL separado. Exemplo:

        alembic upgrade head --sql > revisar.sql
    """
    context.configure(
        url=_url_sincrona(),
        target_metadata=target_metadata,
        literal_binds=True,          # mostra o valor do bind no SQL impresso
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # detecta mudanca de tipo (VARCHAR(20)->TEXT)
        compare_server_default=True, # detecta mudanca de DEFAULT
        include_object=_filtro_de_tabela,
        version_table="alembic_version",
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(conexao: Connection) -> None:
    """Configura e roda as migrations numa conexao ja aberta."""
    context.configure(
        connection=conexao,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=_filtro_de_tabela,
        version_table="alembic_version",
        # Postgres tem ALTER TABLE de verdade, entao nao ha necessidade de
        # modo batch. Deixei False explicito porque o padrao muda entre
        # versoes do Alembic.
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    """
    Cria a engine async e entrega a conexao no formato sincrono.

    O `pool.NullPool` e obrigatorio aqui e nao um detalhe: o Alembic cria e
    descarta a engine a cada comando, e manter um pool aberto segura
    conexao do Postgres depois que o comando terminou.
    """
    connectable = async_engine_from_config(
        {"sqlalchemy.url": _url_assincrona()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        async with connectable.connect() as conexao:
            await conexao.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Modo online: conecta no banco de verdade e aplica."""
    asyncio.run(_run_async_migrations())


# ── 3. O ALEMBIC ESCOLHE O MODO ───────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
