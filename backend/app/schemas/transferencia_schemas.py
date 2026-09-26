"""
================================================================================
MÓDULO: app/schemas/transferencia_schemas.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 1.0.0
OBJETIVO: Define os schemas Pydantic do histórico de transferências entre
          departamentos. Garante que toda transferência seja auditável.
PASTA: backend/app/schemas/
================================================================================

O QUE É TRANSFERÊNCIA
---------------------
O destino do atendimento vem do MENU da empresa, não do canal:

    Cliente entra pelo Canal (tecanologia)
            │
            ▼
    Menu ──► MenuItem ──► Departamento ──► Atendente
                                │
                                ▼
                    (atendente redireciona)
                                │
                                ▼
                    Transferencia (histórico)

Exemplo: a cliente escolheu "1 — Agendamento" no menu, foi atendida no
departamento de Agendamento, mas queria Exames. O atendente transferiu.
Estas schemas existem para que essa operação fique registrada e possa ser
auditada depois: quem transferiu, de onde, para onde e por quê.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoTransferencia


# ============================================
# SCHEMAS DE CRIAÇÃO
# ============================================

class TransferenciaCreate(BaseModel):
    """
    Registro de uma transferência.

    É gravado pelo serviço de atendimento a cada troca de departamento.
    Nunca é aceito como payload de cliente — a API o gera no servidor.
    """

    atendimento_id: int
    tipo: TipoTransferencia = Field(
        TipoTransferencia.ATENDENTE,
        description="menu | atendente | ramal | sistema",
    )

    # ─── Origem ───────────────────────────────────────────────────────────
    departamento_origem_id: Optional[int] = None
    usuario_origem_id: Optional[int] = None
    ramal_origem: Optional[str] = Field(None, max_length=20)

    # ─── Destino ──────────────────────────────────────────────────────────
    departamento_destino_id: Optional[int] = None
    usuario_destino_id: Optional[int] = None
    ramal_destino: Optional[str] = Field(None, max_length=20)

    # ─── Contexto ─────────────────────────────────────────────────────────
    canal_contratado_id: Optional[int] = Field(
        None, description="Canal pelo qual o cliente entrou"
    )
    menu_item_id: Optional[int] = Field(
        None, description="Opção de menu escolhida pelo cliente, se houver"
    )
    motivo: Optional[str] = Field(
        None, description="Justificativa — obrigatória quando tipo = ATENDENTE"
    )


class TransferenciaFiltro(BaseModel):
    """Filtros para consultar o histórico de transferências."""

    atendimento_id: Optional[int] = None
    departamento_origem_id: Optional[int] = None
    departamento_destino_id: Optional[int] = None
    usuario_origem_id: Optional[int] = None
    canal_contratado_id: Optional[int] = None
    tipo: Optional[TipoTransferencia] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class TransferenciaResponse(BaseModel):
    """Transferência retornada pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    atendimento_id: int

    tipo: TipoTransferencia

    departamento_origem_id: Optional[int] = None
    usuario_origem_id: Optional[int] = None
    ramal_origem: Optional[str] = None

    departamento_destino_id: Optional[int] = None
    usuario_destino_id: Optional[int] = None
    ramal_destino: Optional[str] = None

    canal_contratado_id: Optional[int] = None
    menu_item_id: Optional[int] = None
    motivo: Optional[str] = None

    transferido_em: datetime
    criado_em: datetime


__all__ = [
    "TransferenciaCreate",
    "TransferenciaFiltro",
    "TransferenciaResponse",
]
