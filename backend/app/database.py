"""
================================================================================
CONFIGURAÇÃO DE CONEXÃO E SESSÃO DO BANCO DE DADOS (SQLALCHEMY)
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.1.0
Data de Criação: 03 de Julho de 2026
================================================================================
FINALIDADE DO SCRIPT:
Este módulo atua como a camada de abstração de infraestrutura entre a aplicação 
Python e o SGBD. Ele é responsável por centralizar e gerenciar o ciclo de vida 
das conexões com o banco de dados.

Suas responsabilidades principais são:
1. Carregar a string de conexão (DATABASE_URL) de forma segura via variáveis 
   de ambiente, garantindo que credenciais sensíveis não sejam "chumbadas" 
   (hardcoded) no código-fonte.
2. Instanciar a 'Engine' do SQLAlchemy, configurando um pool de conexões 
   resiliente para evitar quedas por inatividade.
3. Definir a fábrica de sessões (SessionLocal) para controle transacional.
4. Prover a classe base (Base) para a declaração dos modelos ORM (Mapeamento 
   Objeto-Relacional).
5. Expor o gerador de dependência (get_db) para injeção automática de sessões 
   nas rotas do FastAPI, garantindo que as conexões sejam abertas e fechadas 
   corretamente a cada requisição HTTP.
================================================================================
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==============================================================================
# 1. CARREGAMENTO E VALIDAÇÃO DE CREDENCIAIS
# ==============================================================================
# O load_dotenv() garante que o arquivo .env seja lido.
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
# A Engine é o motor que gerencia as conexões. 
# MELHORIA DE ENGENHARIA: Adicionamos parâmetros de pool para resiliência:
# - pool_pre_ping=True: Testa se a conexão está viva antes de usá-la. Se o banco 
#   caiu e reiniciou, o SQLAlchemy descarta a conexão morta e cria uma nova, 
#   evitando erros de "Connection refused" ou "Server has gone away".
# - pool_recycle=3600: Recicla (fecha e reabre) as conexões a cada 1 hora. 
#   Isso evita que o SGBD (como PostgreSQL ou MySQL) derrube conexões ociosas 
#   por políticas de timeout de rede ou firewall.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# ==============================================================================
# 3. FÁBRICA DE SESSÕES (SESSIONLOCAL)
# ==============================================================================
# O SessionLocal é uma fábrica que cria sessões de banco de dados.
# - autocommit=False: O commit deve ser explícito (db.commit()), garantindo 
#   controle total sobre a transação.
# - autoflush=False: As alterações não são enviadas automaticamente ao banco 
#   antes de rodar uma query, dando ao desenvolvedor o controle do momento 
#   exato do flush.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================================================
# 4. BASE DECLARATIVA (ORM)
# ==============================================================================
# A classe Base é o "pai" de todos os modelos do sistema (ex: Usuario, Departamento).
# O SQLAlchemy usa essa classe para mapear as classes Python para as tabelas 
# do banco de dados e rastrear os metadados do esquema.
Base = declarative_base()

# ==============================================================================
# 5. INJEÇÃO DE DEPENDÊNCIA PARA O FASTAPI (GET_DB)
# ==============================================================================
# Esta função é um gerador (yield) usado como dependência nas rotas do FastAPI 
# (ex: def listar_usuarios(db: Session = Depends(get_db)):).
# O padrão try/finally garante que, mesmo que ocorra um erro (Exception) durante 
# a requisição, a conexão com o banco (db.close()) será devolvida ao pool, 
# evitando vazamento de memória e esgotamento de conexões no SGBD.
def get_db() -> Generator[Session, None, None]:
    """
    Gerador que fornece uma sessão de banco de dados por requisição.
    Garante o fechamento automático da conexão ao final do ciclo de vida da request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()