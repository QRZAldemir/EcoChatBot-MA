"""
================================================================================
MÓDULO: app/database.py
AUTOR: Aldemir Queiroz da Silva
VERSÃO: 1.2.0
DATA: 03 de Julho de 2026

FINALIDADE:
    Camada de abstração de infraestrutura entre a aplicação Python e o SGBD.
    Centraliza e gerencia o ciclo de vida das conexões com o banco de dados.

RESPONSABILIDADES:
    1. Carregar a string de conexão (DATABASE_URL) via variáveis de ambiente.
    2. Instanciar a Engine do SQLAlchemy com pool de conexões resiliente.
    3. Definir a fábrica de sessões (SessionLocal) para controle transacional.
    4. Prover a classe base (Base) para declaração dos modelos ORM.
    5. Expor o gerador de dependência (get_db) para injeção nas rotas FastAPI.

DEPENDÊNCIAS EXTERNAS:
    - sqlalchemy >= 2.0
    - python-dotenv
    - psycopg2-binary (driver PostgreSQL)
================================================================================
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# ==============================================================================
# 1. CARREGAMENTO E VALIDAÇÃO DE CREDENCIAIS
# ==============================================================================
# O load_dotenv() lê o arquivo .env na raiz do projeto.
# A validação explícita (fail-fast) impede que a aplicação inicie com um banco
# incorreto ou vazio, o que é crucial para evitar corrupção de dados em produção.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "ERRO CRÍTICO: DATABASE_URL não definida. "
        "Copie .env.example para .env e preencha a string de conexão antes de iniciar."
    )

# ==============================================================================
# 2. CRIAÇÃO DA ENGINE E POOL DE CONEXÕES
# ==============================================================================
# A Engine é o motor que gerencia as conexões com o SGBD.
#
# PARÂMETROS DE RESILIÊNCIA:
# - pool_pre_ping=True:
#   Antes de entregar uma conexão ao código, o SQLAlchemy envia um comando
#   leve (ex: SELECT 1) para verificar se a conexão ainda está viva. Se o
#   banco caiu e reiniciou, a conexão morta é descartada e uma nova é criada.
#   Isso evita erros como "Connection refused" ou "Server has gone away".
#
# - pool_recycle=3600:
#   Recicla (fecha e reabre) conexões a cada 1 hora. Previne que o SGBD ou
#   firewalls intermediários derrubem conexões ociosas por timeout de rede.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ==============================================================================
# 3. FÁBRICA DE SESSÕES (SESSIONLOCAL)
# ==============================================================================
# O SessionLocal é uma fábrica (callable) que cria sessões de banco de dados.
#
# - autocommit=False:
#   O commit deve ser explícito (db.commit()), garantindo controle total
#   sobre quando a transação é persistida.
#
# - autoflush=False:
#   As alterações nos objetos ORM não são enviadas automaticamente ao banco
#   antes de executar uma query. O desenvolvedor controla o momento exato
#   do flush, evitando escritas prematuras ou inesperadas.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==============================================================================
# 4. BASE DECLARATIVA (ORM)
# ==============================================================================
# CORREÇÃO APLICADA (v1.2.0):
# A função `declarative_base()` foi descontinuada (deprecated) no SQLAlchemy 2.0.
# A forma moderna e recomendada é criar uma classe que herda de `DeclarativeBase`.
# Isso é compatível com tipagem estática (mypy/pyright) e com os novos recursos
# do SQLAlchemy 2.x, como mapped_column().
#
# Todos os modelos do sistema (Empresa, Usuario, InstanciaChatbot, etc.)
# devem herdar desta classe Base.
class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM do sistema."""
    pass


# ==============================================================================
# 5. INJEÇÃO DE DEPENDÊNCIA PARA O FASTAPI (GET_DB)
# ==============================================================================
# Esta função é um gerador (yield) utilizado como dependência nas rotas do
# FastAPI. Exemplo de uso:
#
#   @router.get("/usuarios")
#   def listar_usuarios(db: Session = Depends(get_db)):
#       return db.query(Usuario).all()
#
# O padrão try/finally garante que, mesmo que ocorra uma exceção durante a
# requisição, a conexão (db.close()) será devolvida ao pool, evitando
# vazamento de memória e esgotamento de conexões no SGBD.
def get_db() -> Generator[Session, None, None]:
    """
    Gerador que fornece uma sessão de banco de dados por requisição HTTP.
    Garante o fechamento automático da conexão ao final do ciclo de vida da request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()