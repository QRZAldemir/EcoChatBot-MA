"""
================================================================================
MÓDULO: app/schemas/atendimento_schemas.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 2.1.0
OBJETIVO: Define os schemas Pydantic do atendimento, do filtro de listagem e da
          transferência entre departamentos. O tipo do canal vem de
          TipoCanalMensageria (app/models/enums.py).
PASTA: backend/app/schemas/
================================================================================

Schemas de Atendimento — alinhados aos models em app/models/.

ENUNS
─────
O tipo do canal NÃO é redefinido aqui. A fonte da verdade é
`TipoCanalMensageria` (app/models/enums.py), com os 9 canais do produto:
whatsapp, telegram, discord, instagram, facebook, pabx, email, webchat, sms.

Até 2026-09 este arquivo mantinha um `TipoCanal(int)` local com apenas
WHATSAPP=1 e INTERNO=2. Isso colidia por nome com o enum oficial e apontava
para o eixo errado: `INTERNO` não é um canal, e os demais canales não
tinham representação. Ver `docs/ESTUDO_DE_CASO_CONTRATO_DE_CANAIS.md`.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TipoCanalMensageria


# ============================================
# ENUMS LOCAIS
# ============================================

class StatusAtendimento(str, Enum):
    ABERTO = "aberto"
    FILA = "fila"
    EM_ATENDIMENTO = "em_atendimento"
    FINALIZADO = "finalizado"


# ============================================
# SCHEMAS DE FILTRO
# ============================================

class FiltroAtendimento(BaseModel):
    """Filtros para listagem de atendimentos."""
    id: Optional[int] = None
    status: Optional[StatusAtendimento] = None
    tipo_canal: Optional[TipoCanalMensageria] = None
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
    tipo_canal: TipoCanalMensageria
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
    """
    Transferência de um atendimento para outro departamento.

    O destino vem do MENU (MenuItem.departamento_id), nunca do canal: o canal
    é a tecnologia de entrada, o departamento é o destino.

    A empresa atendente pode redirecionar o cliente para outro departamento
    (ex.: o cliente escolheu "Agendamento" no menu mas queria "Exames").
    Essa ação precisa ser auditável, então `motivo` e o departamento de
    origem fazem parte do contrato.

    REGISTRO OBRIGATÓRIO
    ---------------------
    Toda transferência gera uma linha em `Transferencia`
    (app/models/transferencia_models.py) com origem, destino, autor e
    horário. Sem esse registro a operação não é concluída.
    """
    usuario_id: int = Field(..., description="Atendente que recebe o atendimento")
    departamento_id: Optional[int] = Field(
        None, description="Departamento de destino — se omitido, mantém o atual"
    )
    canal_id: Optional[int] = Field(
        None, description="Canal de origem, quando a transferência ocorre por ramal"
    )
    departamento_origem_id: Optional[int] = Field(
        None, description="Departamento de onde o cliente veio — para o histórico"
    )
    menu_item_id: Optional[int] = Field(
        None, description="Opção de menu escolhida pelo cliente, se a origem foi o menu"
    )
    ramal_destino: Optional[str] = Field(
        None, max_length=20, description="Ramal de destino em transferências VoIP"
    )
    motivo: Optional[str] = Field(
        None,
        description="Justificativa da transferência — obrigatória quando é o "
                    "atendente que redireciona",
    )


class AtendimentoFinalizar(BaseModel):
    avaliacao: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class AtendimentoResponse(BaseModel):
    id: int
    protocolo: str
    tipo_canal: TipoCanalMensageria
    nome_contato: Optional[str] = None
    telefone: str
    canal_id: Optional[int] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    status: str
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


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
