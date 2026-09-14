# ==============================================================================
# app/security.py
# ──────────────────────────────────────────────────────────────────
# Emissão e verificação do JWT usado pelo painel administrativo.
#
# Antes só existia emissão (em routers/auth.py, só no /login) — nenhuma rota
# verificava o token de volta, então o backend aceitava qualquer requisição
# independente de haver ou não um usuário autenticado. `obter_usuario_atual`
# é a dependency que fecha essa lacuna: valida assinatura, expiração e se o
# token não foi revogado (logout), e é usada tanto por auth.py (/me,
# /refresh, /logout) quanto pelos routers administrativos protegidos em
# main.py.
#
# Variáveis de ambiente:
#     SECRET_KEY          Chave usada para assinar o JWT (obrigatória)
#     JWT_ALGORITHM       Algoritmo de assinatura (padrão: HS256)
#     JWT_EXPIRE_MINUTES  Validade do token em minutos (padrão: 480 = 8h)
# ==============================================================================

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import TokenRevogado, Usuario

logger = logging.getLogger(__name__)

# Hierarquia de acesso (menor → maior). `exigir_nivel_minimo("gerente")`
# aceita gerente e administrador; `exigir_nivel("administrador")` é exato.
NIVEIS_HIERARQUIA = ("atendente", "supervisor", "gerente", "administrador")

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "ERRO CRÍTICO: SECRET_KEY não definida. "
        "Copie .env.example para .env e defina uma chave forte antes de iniciar."
    )

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

_bearer = HTTPBearer(auto_error=False)

_ERRO_NAO_AUTENTICADO = HTTPException(
    status_code=401, detail="Não autenticado.", headers={"WWW-Authenticate": "Bearer"}
)


# ==============================================================================
# EMISSÃO DE TOKEN
# ==============================================================================

def criar_token(usuario: Usuario) -> str:
    """
    Gera um JWT assinado para o usuário autenticado.
    
    O payload inclui:
    - sub: ID do usuário (padrão RFC 7519)
    - jti: Identificador único do token (permite revogação no /logout)
    - nome, email, nivel: Dados do usuário (evitam consultas extras no frontend)
    - iat/exp: Timestamps de emissão e expiração
    """
    # CORREÇÃO: datetime.now(timezone.utc) em vez de datetime.utcnow() (depreciado)
    agora = datetime.now(timezone.utc)
    
    payload = {
        "sub": str(usuario.id),
        "jti": uuid.uuid4().hex,
        "nome": usuario.nome,
        "email": usuario.email,
        "nivel": usuario.nivel.nome if usuario.nivel else None,
        "iat": agora,
        "exp": agora + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    logger.debug(
        "security | Token emitido | user_id=%s | jti=%s | expira_em=%s",
        usuario.id, payload["jti"], payload["exp"].isoformat()
    )
    
    return token


# ==============================================================================
# DECODIFICAÇÃO DE TOKEN
# ==============================================================================

def decodificar_token(token: str) -> dict:
    """
    Valida assinatura e expiração (jose confere "exp" automaticamente).
    Levanta HTTP 401 se o token for inválido, expirado ou malformado.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        # Log de auditoria: ajuda a detectar tentativas de uso de tokens adulterados
        logger.warning("security | Falha na decodificação do JWT: %s", str(e))
        raise _ERRO_NAO_AUTENTICADO


# ==============================================================================
# DEPENDÊNCIA: OBTER USUÁRIO ATUAL (GUARDIÃO DAS ROTAS PROTEGIDAS)
# ==============================================================================

def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependency que protege rotas administrativas.
    
    Fluxo de validação:
    1. Verifica se o header Authorization está presente.
    2. Decodifica e valida o JWT (assinatura + expiração).
    3. Consulta a blacklist (TokenRevogado) para verificar se o token foi revogado.
    4. Busca o usuário no banco de dados (com eager loading do nível).
    5. Verifica se o usuário existe e está ativo.
    
    Retorna o objeto Usuario para injeção nas rotas protegidas.
    """
    if not credenciais:
        raise _ERRO_NAO_AUTENTICADO

    payload = decodificar_token(credenciais.credentials)

    # ── Verificação de revogação (blacklist) ──
    jti = payload.get("jti")
    if jti and db.query(TokenRevogado).filter(TokenRevogado.jti == jti).first():
        # Log de auditoria: token revogado tentando acessar o sistema
        logger.info("security | Token revogado tentou acessar o sistema | jti=%s", jti)
        raise _ERRO_NAO_AUTENTICADO

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise _ERRO_NAO_AUTENTICADO

    # ── Busca do usuário com eager loading do relacionamento 'nivel' ──
    # joinedload evita o problema "N+1 queries" ao acessar usuario.nivel.nome
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.nivel))
        .filter(Usuario.id == int(usuario_id))
        .first()
    )
    
    if not usuario or not usuario.ativo:
        # Log de auditoria: usuário inativo ou inexistente tentando acessar
        logger.warning(
            "security | Acesso negado | user_id=%s | motivo=%s",
            usuario_id, "inativo" if usuario else "inexistente"
        )
        raise _ERRO_NAO_AUTENTICADO

    return usuario


# ==============================================================================
# CONTROLE DE ACESSO BASEADO EM NÍVEL (RBAC)
# ==============================================================================

def _nome_nivel(usuario: Usuario) -> str:
    """Extrai o nome do nível do usuário, normalizado (lowercase, sem espaços)."""
    nome = usuario.nivel.nome if usuario.nivel else ""
    return (nome or "").strip().lower()


def exigir_nivel(*niveis: str):
    """
    Dependency: o usuário autenticado precisa ter um dos níveis (nome exato).
    
    Uso:
        @router.get("/admin", dependencies=[Depends(exigir_nivel("administrador"))])
        def rota_admin():
            ...
    
    Ou com injeção do usuário:
        @router.get("/gerencial")
        def rota_gerencial(usuario: Usuario = Depends(exigir_nivel("gerente", "administrador"))):
            ...
    """
    if not niveis:
        raise ValueError("exigir_nivel() precisa de ao menos um nível")
    permitidos = {n.strip().lower() for n in niveis}

    def _verificador(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        nivel_usuario = _nome_nivel(usuario)
        if nivel_usuario not in permitidos:
            # Log de auditoria: tentativa de acesso com privilégio insuficiente
            logger.warning(
                "security | Privilégio insuficiente | user_id=%s | nivel_atual=%s | niveis_exigidos=%s",
                usuario.id, nivel_usuario, list(permitidos)
            )
            raise HTTPException(status_code=403, detail="Privilégio insuficiente.")
        return usuario

    return _verificador


def exigir_nivel_minimo(nivel: str):
    """
    Dependency: o nível informado ou qualquer um acima na hierarquia.
    
    Hierarquia: atendente < supervisor < gerente < administrador
    
    Exemplo:
        @router.get("/relatorios", dependencies=[Depends(exigir_nivel_minimo("gerente"))])
        def relatorios():
            # Acessível por gerente e administrador
            ...
    """
    chave = nivel.strip().lower()
    try:
        idx = NIVEIS_HIERARQUIA.index(chave)
    except ValueError as exc:
        raise ValueError(f"Nível desconhecido: {nivel}") from exc
    return exigir_nivel(*NIVEIS_HIERARQUIA[idx:])