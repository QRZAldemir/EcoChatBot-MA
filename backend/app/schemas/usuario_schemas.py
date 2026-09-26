# ==============================================================================
# ARQUIVO.....: app/schemas/usuario_schemas.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Schemas Pydantic v2 para Usuario
# VERSÃO......: 3.0.0
# CRIADO EM...: 2024-01-15
# ATUALIZADO..: 2026-09-19
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: FastAPI + Pydantic v2
# ==============================================================================
# DESCRIÇÃO...:
# Define os contratos de entrada e saída (DTOs) para a API do objeto
# Usuario. Utiliza Pydantic v2 com validadores robustos e normalização
# de dados. Cobre CRUD completo, gestão de senha, convites e listagem
# paginada com filtros.
#
# FUNCIONALIDADES:
# 1. Validação de força de senha (mín 8 chars, maiúscula, número, especial)
# 2. Validação de login (usuario) — regex [a-z0-9._-]
# 3. Normalização de email (lowercase, trim)
# 4. Higienização de telefone (apenas dígitos, 10-15 chars)
# 5. Validação de foto (máx 5 MB)
# 6. Schemas para CRUD (Create, Update, Response)
# 7. Schemas para gestão de senha (change, reset)
# 8. Suporte a conexões múltiplas (conexoes_ids)
# 9. Conexão padrão opcional (conexao_padrao_id)
# 10. Vínculo N:M com canais (canais_ids) + canal principal
#
# REGRAS DE VALIDAÇÃO:
# - Senha: 8-128 chars, maiúscula + número + especial, sem espaços
# - Login: 3-50 chars, [a-z0-9._-]
# - Nome: 3-100 chars
# - Email: RFC 5322
# - Telefone: 10-15 dígitos
# - Foto: máx 5 MB
# - conexoes_ids: mínimo 1 item
# - canal_principal_id: se informado, precisa estar em canais_ids
#
# DEPENDÊNCIAS:
# - pydantic>=2.0
# - email-validator
#
# USADO POR:
# - app.routers.tenant.usuario_router (request/response)
# - app.services.usuario_service (validação de entrada)
# ==============================================================================

import re
from datetime import datetime
from typing import List, Optional
from pydantic import (
    BaseModel, ConfigDict, EmailStr, Field,
    field_validator, model_validator,
)


# ==============================================================================
# CONSTANTES DE VALIDAÇÃO
# ==============================================================================
SENHA_MIN: int = 8
SENHA_MAX: int = 128
NOME_MIN: int = 3
NOME_MAX: int = 100
LOGIN_MIN: int = 3
LOGIN_MAX: int = 50
TELEFONE_MIN_DIGITOS: int = 10
TELEFONE_MAX_DIGITOS: int = 15
FOTO_MAX_BYTES: int = 5 * 1024 * 1024
LOGIN_REGEX = re.compile(r"^[a-z0-9._-]+$")


# ==============================================================================
# VALIDADORES REUTILIZÁVEIS
# ==============================================================================
def validar_forca_senha(v: str) -> str:
    """Valida força da senha conforme política de segurança."""
    if any(c.isspace() for c in v):
        raise ValueError("A senha não pode conter espaços")
    if not re.search(r"[A-Z]", v):
        raise ValueError("A senha deve conter ao menos uma letra maiúscula")
    if not re.search(r"[0-9]", v):
        raise ValueError("A senha deve conter ao menos um número")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("A senha deve conter ao menos um caractere especial")
    return v


def limpar_telefone(v: Optional[str]) -> Optional[str]:
    """Remove caracteres não-numéricos e valida tamanho E.164 simplificado."""
    if not v:
        return None
    digits = re.sub(r"\D", "", v)
    if not (TELEFONE_MIN_DIGITOS <= len(digits) <= TELEFONE_MAX_DIGITOS):
        raise ValueError(
            f"Telefone inválido (deve ter entre "
            f"{TELEFONE_MIN_DIGITOS} e {TELEFONE_MAX_DIGITOS} dígitos)"
        )
    return digits


def normaliza_email(v: Optional[str]) -> Optional[str]:
    """Normaliza email para lowercase + trim."""
    return v.lower().strip() if v else v


def normaliza_login(v: Optional[str]) -> Optional[str]:
    """Normaliza login para lowercase + trim."""
    return v.lower().strip() if v else v


def validar_login(v: str) -> str:
    """Valida formato do login (usuario)."""
    if not (LOGIN_MIN <= len(v) <= LOGIN_MAX):
        raise ValueError(f"Login deve ter entre {LOGIN_MIN} e {LOGIN_MAX} caracteres")
    if not LOGIN_REGEX.match(v):
        raise ValueError(
            "Login deve conter apenas letras minúsculas, números, ponto, "
            "underscore ou hífen"
        )
    return v


def strip_nome(v: Optional[str]) -> Optional[str]:
    """Remove espaços nas pontas e garante que nome não fique vazio."""
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Nome é obrigatório")
    return v


def validar_foto(v: Optional[str]) -> Optional[str]:
    """Valida tamanho da foto (base64 ou URL)."""
    if not v:
        return None
    if len(v.encode("utf-8")) > FOTO_MAX_BYTES:
        raise ValueError("Foto excede o tamanho máximo de 5 MB")
    return v


# ==============================================================================
# SCHEMA: ConexaoResponse
# ------------------------------------------------------------------------------
# Representação resumida de uma conexão (telefone da empresa) para
# serialização nas respostas do Usuario.
# ==============================================================================
class ConexaoResponse(BaseModel):
    id: int
    nome_identificador: str
    id_telefone: str
    numero_telefone: Optional[str] = None
    canal_nome: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SCHEMA: CanalVinculoResponse
# ------------------------------------------------------------------------------
# Um canal que o usuário ATENDE, visto pela tabela de junção usuarios_canais.
# Não traz `credenciais`: são segredo do canal, não dado de atendente.
# ==============================================================================
class CanalVinculoResponse(BaseModel):
    id: int
    apelido: str
    tipo: str
    principal: bool
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SCHEMA: VinculosCanalMixin
# ------------------------------------------------------------------------------
# Campos de vínculo N:M usuário <-> canal.
#
# ANTES: `canal_id` (um inteiro) + `turno_id` (que apontava para uma tabela
# `turnos` que nunca existiu). Um atendente ficava preso a UM canal, o que
# não bate com a operação real: o mesmo atendente atende em vários canais.
#
# AGORA: `canais_ids` (lista, gravada em usuarios_canais) + `canal_principal_id`
# marcando o canal de entrada. O canal principal tem que estar na lista — sem
# isso dava para "ter" um principal que não é vínculo do usuário, e o
# roteamento de atendimento pegaria um canal errado.
# ==============================================================================
class VinculosCanalMixin(BaseModel):
    canais_ids: List[int] = Field(default_factory=list)
    canal_principal_id: Optional[int] = None

    @model_validator(mode="after")
    def _principal_pertence_a_lista(self):
        if self.canal_principal_id is not None and self.canal_principal_id not in (
            self.canais_ids or []
        ):
            raise ValueError(
                "canal_principal_id precisa estar contido em canais_ids"
            )
        return self


# ==============================================================================
# SCHEMA: UsuarioCreate
# ------------------------------------------------------------------------------
# Payload para criação de usuário. empresa_id NÃO é exposto — sempre
# extraído do JWT no backend (anti-IDOR). conexoes_ids exige mínimo 1.
# ==============================================================================
class UsuarioCreate(VinculosCanalMixin):
    nome: str = Field(..., min_length=NOME_MIN, max_length=NOME_MAX)
    usuario: str = Field(..., min_length=LOGIN_MIN, max_length=LOGIN_MAX)
    email: EmailStr
    telefone: Optional[str] = None
    senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    foto: Optional[str] = None
    nivel_id: int
    departamento_id: Optional[int] = None
    conexoes_ids: List[int] = Field(default_factory=list, min_length=1)
    conexao_padrao_id: Optional[int] = None
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def _v_nome(cls, v: str) -> str:
        return strip_nome(v)

    @field_validator("usuario")
    @classmethod
    def _v_usuario(cls, v: str) -> str:
        return validar_login(normaliza_login(v))

    @field_validator("email")
    @classmethod
    def _v_email(cls, v: str) -> str:
        return normaliza_email(v)

    @field_validator("telefone")
    @classmethod
    def _v_telefone(cls, v: Optional[str]) -> Optional[str]:
        return limpar_telefone(v)

    @field_validator("senha")
    @classmethod
    def _v_senha(cls, v: str) -> str:
        return validar_forca_senha(v)

    @field_validator("foto")
    @classmethod
    def _v_foto(cls, v: Optional[str]) -> Optional[str]:
        return validar_foto(v)


# ==============================================================================
# SCHEMA: UsuarioConvidar
# ==============================================================================
class UsuarioConvidar(VinculosCanalMixin):
    nome: str = Field(..., min_length=NOME_MIN, max_length=NOME_MAX)
    usuario: str = Field(..., min_length=LOGIN_MIN, max_length=LOGIN_MAX)
    email: EmailStr
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None

    @field_validator("nome")
    @classmethod
    def _v_nome(cls, v: str) -> str:
        return strip_nome(v)

    @field_validator("usuario")
    @classmethod
    def _v_usuario(cls, v: str) -> str:
        return validar_login(normaliza_login(v))

    @field_validator("email")
    @classmethod
    def _v_email(cls, v: str) -> str:
        return normaliza_email(v)


# ==============================================================================
# SCHEMA: UsuarioUpdate
# ------------------------------------------------------------------------------
# Atualização parcial (PATCH-like). empresa_id é IMUTÁVEL.
# ==============================================================================
class UsuarioUpdate(VinculosCanalMixin):
    nome: Optional[str] = Field(None, min_length=NOME_MIN, max_length=NOME_MAX)
    usuario: Optional[str] = Field(None, min_length=LOGIN_MIN, max_length=LOGIN_MAX)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    foto: Optional[str] = None
    senha: Optional[str] = Field(None, min_length=SENHA_MIN, max_length=SENHA_MAX)
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None

    # Em update os dois campos são parciais: ausente = não mexer.
    canais_ids: Optional[List[int]] = None
    canal_principal_id: Optional[int] = None
    conexoes_ids: Optional[List[int]] = None
    conexao_padrao_id: Optional[int] = None

    @field_validator("nome")
    @classmethod
    def _v_nome(cls, v: Optional[str]) -> Optional[str]:
        return strip_nome(v)

    @field_validator("usuario")
    @classmethod
    def _v_usuario(cls, v: Optional[str]) -> Optional[str]:
        return validar_login(normaliza_login(v)) if v else v

    @field_validator("email")
    @classmethod
    def _v_email(cls, v: Optional[str]) -> Optional[str]:
        return normaliza_email(v)

    @field_validator("telefone")
    @classmethod
    def _v_telefone(cls, v: Optional[str]) -> Optional[str]:
        return limpar_telefone(v)

    @field_validator("senha")
    @classmethod
    def _v_senha(cls, v: Optional[str]) -> Optional[str]:
        return validar_forca_senha(v) if v else v

    @field_validator("foto")
    @classmethod
    def _v_foto(cls, v: Optional[str]) -> Optional[str]:
        return validar_foto(v)


# ==============================================================================
# SCHEMA: UsuarioUpdateSenha
# ==============================================================================
class UsuarioUpdateSenha(BaseModel):
    senha_atual: str = Field(..., min_length=1, max_length=SENHA_MAX)
    nova_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    confirmar_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)

    @field_validator("nova_senha")
    @classmethod
    def _v_nova(cls, v: str) -> str:
        return validar_forca_senha(v)

    @model_validator(mode="after")
    def _coincidem(self):
        if self.nova_senha != self.confirmar_senha:
            raise ValueError("As senhas não coincidem")
        return self


# ==============================================================================
# SCHEMA: UsuarioResetSenha
# ==============================================================================
class UsuarioResetSenha(BaseModel):
    nova_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    confirmar_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)

    @field_validator("nova_senha")
    @classmethod
    def _v_nova(cls, v: str) -> str:
        return validar_forca_senha(v)

    @model_validator(mode="after")
    def _coincidem(self):
        if self.nova_senha != self.confirmar_senha:
            raise ValueError("As senhas não coincidem")
        return self


# ==============================================================================
# SCHEMA: UsuarioUpdateStatus
# ==============================================================================
class UsuarioUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)
    motivo: Optional[str] = Field(None, max_length=500)


# ==============================================================================
# SCHEMA: UsuarioResponse
# ------------------------------------------------------------------------------
# Resposta completa com dados expandidos. NÃO expõe senha_hash.
# ==============================================================================
class UsuarioResponse(BaseModel):
    id: int
    empresa_id: int
    empresa_nome: Optional[str] = None
    nome: str
    usuario: str
    email: str
    telefone: Optional[str] = None
    foto: Optional[str] = None
    nivel_id: int
    nivel_nome: Optional[str] = None
    departamento_id: Optional[int] = None
    departamento_nome: Optional[str] = None
    ativo: bool
    status: str
    canais: List[CanalVinculoResponse] = Field(default_factory=list)
    conexoes: List[ConexaoResponse] = Field(default_factory=list)
    conexao_padrao_id: Optional[int] = None
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SCHEMA: UsuarioListItem
# ==============================================================================
class UsuarioListItem(BaseModel):
    id: int
    nome: str
    usuario: str
    email: str
    telefone: Optional[str] = None
    foto: Optional[str] = None
    ativo: bool
    status: str
    nivel_nome: Optional[str] = None
    departamento_nome: Optional[str] = None
    qtd_canais: int = 0
    qtd_conexoes: int = 0


# ==============================================================================
# SCHEMA: UsuarioListResponse
# ==============================================================================
class UsuarioListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[UsuarioListItem]


# ==============================================================================
# SCHEMA: ConviteResponse
# ==============================================================================
class ConviteResponse(BaseModel):
    usuario_id: int
    email: str
    mensagem: str
    link_convite: Optional[str] = None
    expira_em: Optional[datetime] = None