"""
================================================================================
SCRIPT DE INICIALIZAÇÃO E POPULAÇÃO DO BANCO DE DADOS (DATABASE SEEDER)
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.0.0
Data de Criação: 03 de Julho de 2026
================================================================================
FINALIDADE DO SCRIPT:
Este script tem como objetivo realizar a inicialização do esquema do banco de
dados (criação das tabelas via SQLAlchemy) e popular as tabelas base com dados
essenciais (seed data) para o funcionamento da plataforma de atendimento configurável.

Ele garante que os níveis de usuário, departamentos, canais de atendimento e
o usuário administrador estejam corretamente vinculados e prontos para uso
em ambientes de desenvolvimento ou deploy inicial. Os dados de seed em si
(níveis, departamentos, canais, admin e usuários de demonstração) ficam
separados em seed_data.py - este arquivo cuida só da orquestração.
================================================================================
"""

import logging
import os
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

# app.database chama load_dotenv() na importação, garantindo que
# DATABASE_URL/ADMIN_SENHA/SEED_DEMO_USERS estejam disponíveis a partir daqui.
from app.database import engine, Base, SessionLocal
from app.models import NivelUsuario, Departamento, Canal, Usuario
from app.services.usuario_service import hash_senha
from seed_data import (
    NIVEIS_DATA,
    DEPARTAMENTOS_DATA,
    CANAIS_DATA,
    ADMIN_DATA,
    USUARIOS_DEMO_DATA,
)

# Configuração básica de logs para substituir os 'prints' nativos,
# garantindo melhor rastreabilidade em ambientes de produção.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

_VALORES_VERDADEIROS = {"1", "true", "yes", "on"}


def _seed_demo_users_habilitado() -> bool:
    """
    Lê SEED_DEMO_USERS do ambiente (padrão: desligado). Os usuários de
    demonstração (USUARIOS_DEMO_DATA) só são criados quando essa flag está
    ativa - por padrão só o admin de bootstrap é criado, evitando expor
    contas fictícias com senha previsível em ambientes que esqueceram de
    configurar a variável (ex: produção).
    """
    return os.getenv("SEED_DEMO_USERS", "false").strip().lower() in _VALORES_VERDADEIROS


# ==============================================================================
# FUNÇÕES AUXILIARES DE POPULAÇÃO (SEEDERS)
# ==============================================================================

def _resolver_referencia(mapa: Dict[str, object], nome_ref: Optional[str], tipo_ref: str, contexto: str):
    """
    Busca uma referência (nível/departamento/canal) pelo nome no mapa informado.
    Levanta um erro descritivo em vez do KeyError genérico quando o nome
    citado nos dados de seed (ex: 'depto_ref') não existe no mapa, o que
    normalmente indica um erro de digitação em um dos dicionários *_DATA.
    """
    if nome_ref is None:
        return None
    if nome_ref not in mapa:
        disponiveis = ", ".join(sorted(mapa.keys())) or "(nenhum)"
        raise ValueError(
            f"{tipo_ref} '{nome_ref}' referenciado por '{contexto}' não foi encontrado. "
            f"Verifique se o nome está correto e cadastrado antes deste ponto. "
            f"Valores disponíveis: {disponiveis}"
        )
    return mapa[nome_ref]

def _seed_niveis(db: Session) -> Dict[str, NivelUsuario]:
    """Cria os níveis de usuário e retorna um mapa para referência rápida."""
    niveis = [NivelUsuario(**data) for data in NIVEIS_DATA]
    db.add_all(niveis)
    db.flush() # Necessário para gerar os IDs antes do commit final
    return {n.nome: n for n in niveis}

def _seed_departamentos(db: Session) -> Dict[str, Departamento]:
    """Cria os departamentos e retorna um mapa para referência rápida."""
    departamentos = [Departamento(**data) for data in DEPARTAMENTOS_DATA]
    db.add_all(departamentos)
    db.flush()
    return {d.nome: d for d in departamentos}

def _seed_canais(db: Session, depto_map: Dict[str, Departamento]) -> Dict[str, Canal]:
    """Cria os canais vinculando-os aos departamentos através do mapa de referências."""
    canais = []
    for data in CANAIS_DATA:
        canal_data = data.copy()
        depto_ref = canal_data.pop("depto_ref")
        depto = _resolver_referencia(depto_map, depto_ref, "Departamento", canal_data["nome"])
        canal_data["departamento_id"] = depto.id
        canais.append(Canal(**canal_data))

    db.add_all(canais)
    db.flush()
    return {c.nome: c for c in canais}

def _seed_usuarios(
    db: Session,
    usuarios_data: List[dict],
    nivel_map: Dict[str, NivelUsuario],
    depto_map: Dict[str, Departamento],
    canal_map: Dict[str, Canal]
) -> None:
    """Cria os usuários informados aplicando o hash de senha e vinculando às entidades pai."""
    usuarios = []
    for data in usuarios_data:
        usuario_data = data.copy()

        # Mapeamento de IDs das relações
        nivel_ref = usuario_data.pop("nivel_ref")
        nivel = _resolver_referencia(nivel_map, nivel_ref, "Nível de usuário", usuario_data["nome"])
        usuario_data["nivel_id"] = nivel.id

        depto_ref = usuario_data.pop("depto_ref")
        depto = _resolver_referencia(depto_map, depto_ref, "Departamento", usuario_data["nome"])
        usuario_data["departamento_id"] = depto.id if depto else None

        canal_ref = usuario_data.pop("canal_ref")
        canal = _resolver_referencia(canal_map, canal_ref, "Canal", usuario_data["nome"])
        usuario_data["canal_id"] = canal.id if canal else None

        # Aplicação do hash de senha: a partir daqui a senha em texto puro
        # (definida em seed_data.py, ou sobrescrita via ADMIN_SENHA) deixa
        # de existir - só o hash bcrypt é persistido no banco, via
        # Usuario.senha_hash.
        senha_plana = usuario_data.pop("senha")
        usuario_data["senha_hash"] = hash_senha(senha_plana)

        usuarios.append(Usuario(**usuario_data))

    db.add_all(usuarios)


# ==============================================================================
# FUNÇÃO PRINCIPAL DE ORQUESTRAÇÃO
# ==============================================================================

def init_db() -> None:
    """
    Função principal para inicializar o banco de dados.
    Cria as tabelas (se não existirem) e popula com dados iniciais (seed).
    Utiliza gerenciamento de contexto para garantir o fechamento da sessão.
    """
    logger.info("Iniciando processo de criação das tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)

    # O uso do 'with' garante que a sessão será fechada corretamente ao final,
    # mesmo em caso de exceções, eliminando a necessidade do bloco 'finally'.
    with SessionLocal() as db:
        try:
            # Verificação de idempotência: evita duplicação de dados em execuções repetidas
            if db.query(NivelUsuario).count() > 0:
                logger.info("Banco de dados já possui dados iniciais. Processo de seed ignorado.")
                return

            logger.info("Banco de dados vazio. Iniciando população (seed) dos dados básicos...")

            # Execução dos seeders em ordem de dependência
            nivel_map = _seed_niveis(db)
            depto_map = _seed_departamentos(db)
            canal_map = _seed_canais(db, depto_map)

            # A conta admin sempre é criada; ADMIN_SENHA permite sobrescrever
            # a senha padrão do seed sem editar código-fonte (recomendado
            # fora de ambiente local de desenvolvimento).
            admin_data = ADMIN_DATA.copy()
            admin_data["senha"] = os.getenv("ADMIN_SENHA", admin_data["senha"])

            seed_demo = _seed_demo_users_habilitado()
            usuarios_data = [admin_data] + (USUARIOS_DEMO_DATA if seed_demo else [])

            _seed_usuarios(db, usuarios_data, nivel_map, depto_map, canal_map)

            # Consolidação da transação
            db.commit()

            logger.info("✅ Banco de dados inicializado e populado com sucesso!")
            logger.info(f"   - {len(nivel_map)} níveis de usuário criados.")
            logger.info(f"   - {len(depto_map)} departamentos criados.")
            logger.info(f"   - {len(canal_map)} canais de atendimento criados.")
            if seed_demo:
                logger.info(f"   - {len(usuarios_data)} usuários criados (1 admin + {len(USUARIOS_DEMO_DATA)} de demonstração).")
            else:
                logger.info(f"   - {len(usuarios_data)} usuário criado (apenas admin; SEED_DEMO_USERS não está ativo).")
            # A senha nunca é escrita no log: mesmo sendo INFO hoje, logs
            # tendem a acabar em arquivo/serviço de observabilidade cedo ou
            # tarde, e uma credencial ali é uma credencial vazada.
            origem_senha = "variável de ambiente ADMIN_SENHA" if os.getenv("ADMIN_SENHA") else "padrão de seed_data.py (defina ADMIN_SENHA para trocar)"
            logger.info(f"📧 Login administrativo: {admin_data['email']} - senha definida via {origem_senha}.")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro crítico ao inicializar o banco de dados: {e}")
            raise


if __name__ == "__main__":
    init_db()
