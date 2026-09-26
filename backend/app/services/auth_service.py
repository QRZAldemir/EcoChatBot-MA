"""
================================================================================
MÓDULO: app/services/auth_service.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.0.0 (Implementação inicial de Autenticação e Multi-Tenancy)

DESCRIÇÃO:
    Centraliza toda a lógica de segurança, autenticação e manipulação de tokens 
    JWT (JSON Web Tokens). Este módulo é responsável por garantir que apenas 
    usuários legítimos acessem o sistema e que o isolamento de dados (multi-tenancy) 
    seja respeitado em cada requisição.

RESPONSABILIDADES:
    1. Hash e verificação de senhas utilizando o algoritmo Bcrypt (padrão de 
       mercado para armazenamento seguro de credenciais).
    2. Geração de tokens JWT contendo o identificador do usuário (sub), o 
       identificador da empresa (empresa_id) e o nível de acesso (nivel).
    3. Validação e decodificação de tokens JWT, garantindo integridade, 
       autenticidade e expiração.

DEPENDÊNCIAS EXTERNAS (requirements.txt):
    - python-jose[cryptography]  -> Para manipulação de JWT.
    - passlib[bcrypt]            -> Para hash de senhas.

PÚBLICO-ALVO DA DOCUMENTAÇÃO:
    Desenvolvedores da equipe que precisam entender o fluxo de login, a estrutura 
    do payload do JWT e como o isolamento de tenant é garantido via token.
================================================================================
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Carrega variáveis de ambiente
load_dotenv()
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. CONFIGURAÇÕES DE SEGURANÇA E CRIPTOGRAFIA
# ==============================================================================

# SECRET_KEY: Chave secreta usada para assinar o token. 
# CRÍTICO: Em produção, esta chave DEVE ser uma string longa, aleatória e 
# gerada criptograficamente (ex: openssl rand -hex 32). Nunca use "segredo123".
# Fonte única de verdade: app.config.Settings (alias JWT_SECRET no .env da raiz).
# A validação de força fica em Settings.check_secret_key_strength, que só aborta
# em produção. Aqui resta apenas o corte de chave vazia/vazia-padrão.
SECRET_KEY = settings.secret_key
if not SECRET_KEY or SECRET_KEY == "changeme":
    raise RuntimeError(
        "ERRO CRÍTICO DE SEGURANÇA: JWT_SECRET não definida ou é o valor padrão. "
        "Gere uma chave segura (ex: openssl rand -hex 32) e defina-a no .env "
        "antes de iniciar a aplicação."
    )

# Aviso explícito: o .env de desenvolvimento ainda traz a chave de exemplo.
# Não bloqueia o ambiente de desenvolvimento, mas é obrigatório rotacionar
# antes de qualquer deploy.
CHAVES_DE_EXEMPLO = {"troque-por-uma-chave-secreta-de-64-caracteres"}
if SECRET_KEY in CHAVES_DE_EXEMPLO:
    logger.warning(
        "JWT_SECRET em modo de exemplo: rotacione a chave antes de qualquer deploy."
    )

# ALGORITHM: Algoritmo de assinatura. HS256 (HMAC com SHA-256) é simétrico e 
# adequado para sistemas onde o mesmo servidor emite e valida o token.
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# ACCESS_TOKEN_EXPIRE_MINUTES: Tempo de vida do token. 
# Para sistemas corporativos, 30 a 60 minutos é o recomendado. Tokens de longa 
# duração aumentam a janela de risco em caso de roubo de credenciais.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ==============================================================================
# 2. CONTEXTO DE CRIPTOGRAFIA DE SENHAS (PASSLIB)
# ==============================================================================
# O CryptContext gerencia o hash de senhas. 
# schemes=["bcrypt"]: Define o Bcrypt como algoritmo padrão. O Bcrypt é lento 
# por design, o que o torna resistente a ataques de força bruta (GPU/ASIC).
# deprecated="auto": Marca automaticamente hashes de algoritmos mais antigos 
# (como md5 ou sha256) como obsoletos, permitindo migração transparente.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """
    Gera o hash Bcrypt de uma senha em texto puro.
    
    Por que usar esta função?
    Nunca armazene senhas em texto puro no banco de dados. Se o banco for 
    comprometido, os hashes do Bcrypt ainda exigirão um esforço computacional 
    massivo para serem revertidos, protegendo os usuários.
    
    Args:
        senha (str): A senha em texto puro digitada pelo usuário.
        
    Returns:
        str: O hash da senha, pronto para ser salvo no campo `senha_hash` do DB.
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_texto_puro: str, senha_hash_do_db: str) -> bool:
    """
    Compara uma senha em texto puro com o hash armazenado no banco de dados.
    
    Args:
        senha_texto_puro (str): A senha fornecida no formulário de login.
        senha_hash_do_db (str): O hash recuperado do banco de dados.
        
    Returns:
        bool: True se a senha estiver correta, False caso contrário.
    """
    return pwd_context.verify(senha_texto_puro, senha_hash_do_db)


# ==============================================================================
# 3. GERAÇÃO E VALIDAÇÃO DE TOKENS JWT
# ==============================================================================

def criar_token_acesso(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria e assina um token JWT com os dados do usuário e do tenant (empresa).
    
    Estrutura do Payload (Claims):
    - "sub" (Subject): Identificador único do usuário (user_id). É o padrão RFC 7519.
    - "empresa_id": O ID da empresa (tenant). Essencial para o multi-tenancy.
    - "nivel": O perfil de acesso (ex: "super_admin", "admin", "atendente").
    - "exp" (Expiration): Timestamp de quando o token expira.
    
    Args:
        data (dict): Dicionário contendo 'sub', 'empresa_id' e 'nivel'.
        expires_delta (timedelta, optional): Tempo de expiração customizado.
        
    Returns:
        str: O token JWT codificado em string.
    """
    to_encode = data.copy()
    
    # Calcula o tempo de expiração
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    # Adiciona a claim de expiração ao payload
    to_encode.update({"exp": expire})
    
    # Assina o token usando a chave secreta e o algoritmo definido
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.debug("auth_service | Token JWT gerado para user_id=%s, empresa_id=%s", 
                 data.get("sub"), data.get("empresa_id"))
                 
    return encoded_jwt


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Valida a assinatura, verifica a expiração e decodifica o payload do token JWT.
    
    Esta função é chamada pela dependência `get_current_user_tenant` em `deps.py`.
    Ela atua como o "guardião" da aplicação, rejeitando qualquer token que tenha 
    sido adulterado (assinatura inválida) ou que esteja fora do prazo de validade.
    
    Args:
        token (str): O token JWT extraído do header "Authorization".
        
    Returns:
        dict: O payload decodificado contendo 'sub', 'empresa_id', 'nivel', etc.
        
    Raises:
        HTTPException 401: Se o token for inválido, expirado ou malformado.
    """
    # Credenciais padrão para o cabeçalho WWW-Authenticate em caso de erro
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # O método decode faz três coisas cruciais:
        # 1. Verifica se a assinatura bate com o SECRET_KEY.
        # 2. Verifica se o token não expirou (claim 'exp').
        # 3. Decodifica o payload (JSON) para um dicionário Python.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return payload
        
    except JWTError as e:
        # Captura qualquer erro específico da biblioteca jose (expirado, assinatura errada, etc.)
        logger.warning("auth_service | Falha na validação do JWT: %s", str(e))
        raise credentials_exception
    except Exception as e:
        # Captura erros inesperados (ex: token não é uma string, formato JSON inválido)
        logger.error("auth_service | Erro inesperado ao decodificar token: %s", str(e))
        raise credentials_exception