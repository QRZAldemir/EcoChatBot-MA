"""
app/routers/auth.py
──────────────────────────────────────────────────────────────────
Autenticação do painel administrativo: login com e-mail/senha, emissão de
JWT, e as rotas que dependem dele (/me, /refresh, /logout).

A verificação do token em si (assinatura, expiração, revogação) mora em
app/security.py, reaproveitada aqui e pelos routers administrativos
protegidos (ver ROUTERS_CONFIG em main.py).
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TokenRevogado, Usuario
from app.security import criar_token, decodificar_token, obter_usuario_atual
from app.services.usuario_service import UsuarioService, verificar_senha

router = APIRouter()

_bearer = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    senha: str


class UsuarioLogado(BaseModel):
    id: int
    nome: str
    email: str
    nivel: Optional[str] = None
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioLogado


def _usuario_logado(usuario: Usuario) -> UsuarioLogado:
    return UsuarioLogado(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        nivel=usuario.nivel.nome if usuario.nivel else None,
        departamento_id=usuario.departamento_id,
        canal_id=usuario.canal_id,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica um usuário do painel administrativo por e-mail/senha e
    retorna um JWT para as próximas requisições.
    """
    # Mesma mensagem de erro tanto para e-mail inexistente quanto para
    # senha errada — evita que a resposta revele se um e-mail está cadastrado.
    erro_credenciais = HTTPException(status_code=401, detail="E-mail ou senha inválidos.")

    usuario = UsuarioService.buscar_por_email(db, body.email)
    if not usuario or not verificar_senha(body.senha, usuario.senha_hash):
        raise erro_credenciais

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo. Fale com um administrador.")

    return LoginResponse(access_token=criar_token(usuario), usuario=_usuario_logado(usuario))


@router.get("/me", response_model=UsuarioLogado)
def me(usuario: Usuario = Depends(obter_usuario_atual)):
    """Devolve o usuário do token atual — usado pelo frontend para validar a sessão no boot da app."""
    return _usuario_logado(usuario)


@router.post("/refresh", response_model=LoginResponse)
def refresh(usuario: Usuario = Depends(obter_usuario_atual)):
    """Emite um novo token a partir de um token ainda válido, sem exigir login de novo."""
    return LoginResponse(access_token=criar_token(usuario), usuario=_usuario_logado(usuario))


@router.post("/logout", status_code=204)
def logout(credenciais: HTTPAuthorizationCredentials = Depends(_bearer), db: Session = Depends(get_db)):
    """
    Revoga o token atual — necessário porque JWT é stateless por natureza;
    sem isso, um token roubado continuaria válido até expirar mesmo depois
    do usuário sair. Ver TokenRevogado em app/models.
    """
    payload = decodificar_token(credenciais.credentials)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        db.merge(TokenRevogado(jti=jti, expira_em=datetime.utcfromtimestamp(exp)))
        db.commit()
    return None


@router.post("/validate")
def validate_token(credenciais: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Valida se o token atual é válido (não revogado e não expirado)."""
    try:
        payload = decodificar_token(credenciais.credentials)
        return {"valid": True}
    except HTTPException:
        return {"valid": False}
