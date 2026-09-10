"""
Schemas de Usuário — multi-tenant, alinhados ao modelo real em app/models/__init__.py.

O modelo Usuario usa nivel_id (FK para tabela nivel_usuario), departamento_id,
canal_id, ativo (bool) e status (string). NivelUsuario é uma tabela com nome
('atendente'|'supervisor'|'gerente'|'administrador').

Melhorias de segurança aplicadas:
- Senha com comprimento mínimo maior e validação de força (maiúscula, número,
  caractere especial) e proibição de espaços.
- Campos de texto livre (motivo, telefone, nome) com limite de tamanho.
- Normalização de email para minúsculas.
- Campos opcionais com default explícito (None) para evitar estado compartilhado.
"""

import re
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# ============================================
# VALIDADORES REUTILIZÁVEIS
# ============================================

_SENHA_MIN = 8


def _validar_forca_senha(v: str) -> str:
    """Exige pelo menos 1 maiúscula, 1 número e 1 caractere especial; sem espaços."""
    if any(ch.isspace() for ch in v):
        raise ValueError("A senha não pode conter espaços")
    if not re.search(r"[A-Z]", v):
        raise ValueError("A senha deve conter ao menos uma letra maiúscula")
    if not re.search(r"[0-9]", v):
        raise ValueError("A senha deve conter ao menos um número")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("A senha deve conter ao menos um caractere especial")
    return v


def _limpar_telefone(v: Optional[str]) -> Optional[str]:
    """Remove não-dígitos e valida tamanho, retornando apenas números."""
    if not v:
        return None
    cleaned = re.sub(r"[^0-9]", "", v)
    if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValueError("Telefone inválido (deve ter entre 10 e 15 dígitos)")
    return cleaned


# ============================================
# SCHEMAS DE CRIAÇÃO
# ============================================

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    telefone: Optional[str] = None
    senha: str = Field(..., min_length=_SENHA_MIN, max_length=128)
    nivel_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("email")
    @classmethod
    def _normaliza_email(cls, v):
        return v.lower()

    @field_validator("telefone")
    @classmethod
    def _valida_telefone(cls, v):
        return _limpar_telefone(v)

    @field_validator("senha")
    @classmethod
    def _valida_senha(cls, v):
        return _validar_forca_senha(v)


class UsuarioCreateAdmin(UsuarioCreate):
    """Usuário criado pelo admin (já ativo)."""
    ativo: bool = True


class UsuarioConvidar(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    nivel_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("email")
    @classmethod
    def _normaliza_email(cls, v):
        return v.lower()


# ============================================
# SCHEMAS DE ATUALIZAÇÃO
# ============================================

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: Optional[bool] = None

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("email")
    @classmethod
    def _normaliza_email(cls, v):
        return v.lower() if v is not None else v

    @field_validator("telefone")
    @classmethod
    def _valida_telefone(cls, v):
        return _limpar_telefone(v)


class UsuarioUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)
    motivo: Optional[str] = Field(None, max_length=500)


class _SenhaMixin(BaseModel):
    """Base com validação de força e confirmação de senha."""

    nova_senha: str = Field(..., min_length=_SENHA_MIN, max_length=128)
    confirmar_senha: str = Field(..., min_length=_SENHA_MIN, max_length=128)

    @field_validator("nova_senha")
    @classmethod
    def _valida_senha(cls, v):
        return _validar_forca_senha(v)

    @field_validator("confirmar_senha")
    @classmethod
    def _confere(cls, v, info):
        if "nova_senha" in info.data and v != info.data["nova_senha"]:
            raise ValueError("As senhas não coincidem")
        return v


class UsuarioUpdateSenha(_SenhaMixin):
    senha_atual: str = Field(..., min_length=1, max_length=128)


class UsuarioResetSenha(_SenhaMixin):
    """Reset de senha pelo admin."""


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class UsuarioResponse(BaseModel):
    id: int
    cliente_id: Optional[int] = None
    nome: str
    email: str
    telefone: Optional[str] = None
    nivel_id: int
    nivel_nome: Optional[str] = None
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: bool
    status: str
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[UsuarioResponse]


class ConviteResponse(BaseModel):
    usuario_id: int
    email: str
    mensagem: str
    link_convite: Optional[str] = None
    expira_em: Optional[datetime] = None
