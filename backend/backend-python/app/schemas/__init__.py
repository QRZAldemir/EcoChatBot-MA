from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ━━━ Nível Usuario ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class NivelUsuarioBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class NivelUsuarioCreate(NivelUsuarioBase):
    pass

class NivelUsuarioResponse(NivelUsuarioBase):
    id: int
    
    class Config:
        from_attributes = True

# ━━━ Departamento ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DepartamentoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class DepartamentoResponse(DepartamentoBase):
    id: int
    criado_em: datetime
    
    class Config:
        from_attributes = True

# ━━━ Canal ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CanalBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    arquivo_menu: str
    departamento_id: Optional[int] = None
    ativo: bool = True

class CanalCreate(CanalBase):
    pass

class CanalUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    arquivo_menu: Optional[str] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None

class CanalResponse(CanalBase):
    id: int
    criado_em: datetime
    departamento: Optional[DepartamentoResponse] = None
    
    class Config:
        from_attributes = True

# ━━━ Usuario ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    nivel_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    senha: str  # Senha em texto claro (será hasheada no backend)

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None  # Opcional - só atualiza se fornecida

class UsuarioResponse(UsuarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    nivel: Optional[NivelUsuarioResponse] = None
    departamento: Optional[DepartamentoResponse] = None
    canal: Optional[CanalResponse] = None
    
    class Config:
        from_attributes = True

# Para listagem sem dados sensíveis
class UsuarioListItem(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str] = None
    ativo: bool
    nivel_nome: Optional[str] = None
    departamento_nome: Optional[str] = None
    canal_nome: Optional[str] = None
    
    class Config:
        from_attributes = True
