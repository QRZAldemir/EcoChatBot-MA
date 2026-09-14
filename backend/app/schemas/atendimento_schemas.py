"""
Schemas de Atendimento — alinhados ao modelo real em app/models/__init__.py.

Enums definidos localmente para evitar dependência de módulos inexistentes.
Campos mapeados conforme colunas reais da tabela 'atendimentos'.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ============================================
# ENUMS LOCAIS
# ============================================

class StatusAtendimento(str, Enum):
    ABERTO = "aberto"
    FILA = "fila"
    EM_ATENDIMENTO = "em_atendimento"
    FINALIZADO = "finalizado"


class TipoCanal(int, Enum):
    WHATSAPP = 1
    INTERNO = 2


# ============================================
# SCHEMAS DE FILTRO
# ============================================

class FiltroAtendimento(BaseModel):
    """Filtros para listagem de atendimentos."""
    id: Optional[int] = None
    status: Optional[StatusAtendimento] = None
    tipo_canal: Optional[TipoCanal] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cliente_whatsapp: Optional[str] = None
    protocolo: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    ativo: Optional[bool] = True

    @field_validator('data_inicio', 'data_fim', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


# ============================================
# SCHEMAS DE CRIAÇÃO
# ============================================

class AtendimentoCreate(BaseModel):
    tipo_canal: TipoCanal
    paciente_telefone: str = Field(..., min_length=10)
    paciente_nome: Optional[str] = None
    paciente_email: Optional[str] = None
    canal_id: Optional[int] = None
    departamento_id: Optional[int] = None

    @field_validator('paciente_telefone')
    @classmethod
    def validate_phone(cls, v):
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 10:
            raise ValueError('Telefone inválido')
        return cleaned


# ============================================
# SCHEMAS DE ATUALIZAÇÃO
# ============================================

class AtendimentoUpdate(BaseModel):
    paciente_nome: Optional[str] = None
    paciente_telefone: Optional[str] = None
    paciente_email: Optional[str] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    canal_id: Optional[int] = None
    status: Optional[StatusAtendimento] = None


class AtendimentoTransferir(BaseModel):
    usuario_id: int
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None


class AtendimentoFinalizar(BaseModel):
    avaliacao: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class AtendimentoResponse(BaseModel):
    id: int
    protocolo: str
    tipo_canal: int
    nome_contato: Optional[str] = None
    telefone: str
    canal_id: Optional[int] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    status: str
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class AtendimentoDetalhado(AtendimentoResponse):
    tempo_espera_minutos: Optional[float] = None
    tempo_atendimento_minutos: Optional[float] = None


class AtendimentoIndicadores(BaseModel):
    total: int
    aberto: int
    fila: int
    em_atendimento: int
    finalizado_humano: int
    finalizado_sem_atendente: int
    por_departamento: List[dict]
    tempo_medio_espera: Optional[float] = None
    tempo_medio_atendimento: Optional[float] = None
