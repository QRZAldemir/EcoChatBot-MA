"""
Schemas de Usuário — multi-tenant, alinhados ao modelo real em app/models/__init__.py.

O modelo Usuario usa nivel_id (FK para tabela nivel_usuario), departamento_id,
canal_id, ativo (bool) e status (string). NivelUsuario é uma tabela com nome
('atendente'|'supervisor'|'gerente'|'administrador').
"""

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================
# SCHEMAS DE CRIAÇÃO
# ============================================

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    telefone: Optional[str] = None
    senha: str = Field(..., min_length=6)
    nivel_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: bool = True

    @field_validator('nome')
    @classmethod
    def _strip_nome(cls, v):
        return v.strip()


class UsuarioCreateAdmin(UsuarioCreate):
    """Usuário criado pelo admin (já ativo)."""
    ativo: bool = True


class UsuarioConvidar(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    nivel_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None


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


class UsuarioUpdateStatus(BaseModel):
    status: str
    motivo: Optional[str] = None


class UsuarioUpdateSenha(BaseModel):
    senha_atual: str = Field(..., min_length=6)
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)

    @field_validator('confirmar_senha')
    @classmethod
    def _confere(cls, v, info):
        if 'nova_senha' in info.data and v != info.data['nova_senha']:
            raise ValueError('As senhas não coincidem')
        return v


class UsuarioResetSenha(BaseModel):
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)

    @field_validator('confirmar_senha')
    @classmethod
    def _confere(cls, v, info):
        if 'nova_senha' in info.data and v != info.data['nova_senha']:
            raise ValueError('As senhas não coincidem')
        return v


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
