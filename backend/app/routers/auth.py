"""
app/routers/auth.py
──────────────────────────────────────────────────────────────────
Autenticação do painel administrativo: login com e-mail/senha e emissão
de JWT. Usa o hash de senha (bcrypt) já existente em usuario_service.py.

Variáveis de ambiente:
    SECRET_KEY          Chave usada para assinar o JWT (obrigatória)
    JWT_ALGORITHM       Algoritmo de assinatura (padrão: HS256)
    JWT_EXPIRE_MINUTES  Validade do token em minutos (padrão: 480 = 8h)
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.services.usuario_service import UsuarioService, verificar_senha

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "ERRO CRÍTICO: SECRET_KEY não definida. "
        "Copie .env.example para .env e defina uma chave forte antes de iniciar."
    )

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))


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


def _criar_token(usuario: Usuario) -> str:
    expira_em = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(usuario.id),
        "nome": usuario.nome,
        "email": usuario.email,
        "nivel": usuario.nivel.nome if usuario.nivel else None,
        "exp": expira_em,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


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

    token = _criar_token(usuario)
    return LoginResponse(
        access_token=token,
        usuario=UsuarioLogado(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            nivel=usuario.nivel.nome if usuario.nivel else None,
            departamento_id=usuario.departamento_id,
            canal_id=usuario.canal_id,
        ),
    )
