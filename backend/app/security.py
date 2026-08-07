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

import os
import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TokenRevogado, Usuario

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


def criar_token(usuario: Usuario) -> str:
    agora = datetime.utcnow()
    payload = {
        "sub": str(usuario.id),
        "jti": uuid.uuid4().hex,   # identifica este token específico — permite revogar no /logout
        "nome": usuario.nome,
        "email": usuario.email,
        "nivel": usuario.nivel.nome if usuario.nivel else None,
        "iat": agora,
        "exp": agora + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Valida assinatura e expiração (jose confere "exp" automaticamente); levanta 401 se inválido."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise _ERRO_NAO_AUTENTICADO


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependency que protege rotas administrativas: exige um JWT válido, não expirado e não revogado."""
    if not credenciais:
        raise _ERRO_NAO_AUTENTICADO

    payload = decodificar_token(credenciais.credentials)

    jti = payload.get("jti")
    if jti and db.query(TokenRevogado).filter(TokenRevogado.jti == jti).first():
        raise _ERRO_NAO_AUTENTICADO

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise _ERRO_NAO_AUTENTICADO

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if not usuario or not usuario.ativo:
        raise _ERRO_NAO_AUTENTICADO

    return usuario
