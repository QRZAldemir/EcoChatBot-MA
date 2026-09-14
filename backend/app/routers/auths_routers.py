"""
================================================================================
MÓDULO: app/routers/auth.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.0.0

DESCRIÇÃO:
    Contém os endpoints de autenticação do sistema. O endpoint principal 
    (/login) orquestra a busca do usuário no banco de dados, a verificação 
    segura da senha (via Bcrypt) e a emissão do token JWT contendo o 
    contexto do tenant (empresa_id).

FLUXO DE EXECUÇÃO DO LOGIN:
    1. Cliente envia POST /api/auth/login com {email, senha}.
    2. FastAPI valida os dados de entrada usando o schema LoginRequest.
    3. O sistema busca o usuário no banco pelo e-mail.
    4. Se o usuário não existir ou estiver inativo, retorna 401 (genérico 
       para não vazar se o e-mail existe ou não, prevenindo enumeração).
    5. O sistema compara a senha enviada com o hash armazenado (Bcrypt).
    6. Se a senha estiver incorreta, retorna 401.
    7. Se tudo estiver correto, gera o token JWT com sub, empresa_id e nivel.
    8. Retorna o token e metadados do usuário para o cliente.

REGISTRO EM main.py:
    app.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])
================================================================================
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import verificar_senha, criar_token_acesso

router = APIRouter()
logger = logging.getLogger(__name__)


# ==============================================================================
# ENDPOINT: LOGIN
# ==============================================================================
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_usuario(
    dados_login: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário e emite um token JWT com o contexto do tenant (empresa).
    
    Este endpoint é o ponto de entrada para a obtenção de credenciais. 
    Ele foi desenhado com foco em segurança, evitando vazamento de informações 
    sobre a existência de usuários (prevenindo ataques de enumeração de contas).
    
    Args:
        dados_login (LoginRequest): Schema Pydantic contendo email e senha.
        db (Session): Sessão do banco de dados injetada pelo FastAPI.
        
    Returns:
        TokenResponse: Contém o access_token, token_type, user_id e empresa_id.
        
    Raises:
        HTTPException 401: Se as credenciais forem inválidas ou o usuário inativo.
    """
    
    # ── 1. BUSCA DO USUÁRIO NO BANCO DE DADOS ──
    # Utilizamos .first() para evitar erros caso existam duplicatas acidentais,
    # embora o campo email deva ser único (constraint no modelo).
    usuario: Usuario | None = db.query(Usuario).filter(
        Usuario.email == dados_login.email
    ).first()

    # ── 2. VALIDAÇÃO DE EXISTÊNCIA E STATUS ──
    # NOTA DE SEGURANÇA: A mensagem de erro é propositalmente genérica 
    # ("Credenciais inválidas"). Se retornássemos "E-mail não encontrado", 
    # um atacante poderia usar este endpoint para descobrir quais e-mails 
    # estão cadastrados no sistema (User Enumeration Attack).
    if not usuario:
        logger.warning("auth | Tentativa de login com e-mail inexistente: %s", dados_login.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        logger.warning("auth | Tentativa de login de usuário inativo: %s (ID: %s)", dados_login.email, usuario.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── 3. VERIFICAÇÃO DA SENHA (BCRYPT) ──
    # O passlib (via auth_service) extrai o salt do hash armazenado e 
    # recalcula o hash da senha fornecida para comparar.
    if not verificar_senha(dados_login.senha, usuario.senha_hash):
        logger.warning("auth | Tentativa de login com senha incorreta para o e-mail: %s", dados_login.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── 4. EMISSÃO DO TOKEN JWT ──
    # O payload do token contém as "claims" (afirmações) sobre o usuário.
    # O 'sub' (subject) é o padrão RFC 7519 para identificar o usuário.
    # O 'empresa_id' é a base do nosso isolamento multi-tenant.
    dados_token = {
        "sub": str(usuario.id),       # Convertido para string, pois o padrão JWT prefere strings no 'sub'
        "empresa_id": usuario.empresa_id,
        "nivel": usuario.perfil       # Mapeado como 'nivel' para consistência com o deps.py
    }
    
    access_token = criar_token_acesso(data=dados_token)

    logger.info("auth | Login bem-sucedido: user_id=%s, empresa_id=%s", usuario.id, usuario.empresa_id)

    # ── 5. RESPOSTA AO CLIENTE ──
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=usuario.id,
        empresa_id=usuario.empresa_id
    )