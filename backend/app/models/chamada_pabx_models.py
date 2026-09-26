"""
EcoChatBot-MA - Chamada PABX (VoIP) / BILHETAGEM
@file chamada_pabx_models.py | @version 3.0.0 | @author Aldemir Queiroz

POR QUE ESTE MODEL MUDOU TANTO
------------------------------
A v2.0.0 foi escrita contra a INTENCAO do projeto, nao contra o banco. A
tabela `chamadas_pabx` foi criada pela migration 004 e as colunas tem
outros nomes:

    conceito    coluna no BANCO         model v2 (errado)
    ---------   ---------------------   --------------------
    id da call  pabx_call_id UNIQUE     call_id
    origem      numero_origem           ramal_origem
    destino     numero_destino          ramal_destino
    duracao     duracao_segundos        duracao_seg
    gravacao    url_gravacao            gravacao_url
    tenant      cliente_id NOT NULL     (nao existia)
    resumo IA   resumo_ia               (PERDIDO)

O v2 ainda guardava `ramal_origem` E `numero_origem` com a mesma
informacao, sem regra dizendo qual manda.

DECISAO: O CODIGO SEGUIR O BANCO (opcao A)
-----------------------------------------
Em vez de exigir reescrita dos dados ja gravados, o model passou a usar os
nomes que o banco ja tem. As duplicatas sairam em vez de ficarem: dois
lugares com o mesmo dado e receita de bug silencioso. `numero_externo`
tambem saiu - o numero do cliente externo e um dos dois lados, nao um
terceiro fato.

AUDITORIA - LEIA ANTES DE MEXER
-------------------------------
1. O DDL antigo tinha ON DELETE CASCADE em cliente_id e canal_id: apagar
   um cliente ou um canal APAGAVA A BILHETAGEM. A migration 010 derruba
   esses CASCADE. Nao reintroduza.
2. `pabx_call_id` e a chave de idempotencia. O PABX reenvia evento; sem
   UNIQUE a mesma ligacao seria bilhetada duas vezes.
3. `gravacao_hash` e SHA-256 do audio. Sem ele nao da para provar que a
   gravacao nao foi trocada depois. So URL nao prova nada.
4. Nenhum delete() fisico. O soft delete sustenta a auditoria.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusChamada, TipoChamada
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.canal_models import CanalContratado


class ChamadaPABX(TimestampMixin, TenantMixin, SoftDeleteMixin, Base):
    """Registro de uma chamada VoIP (entrada, saida ou interna)."""

    __tablename__ = "chamadas_pabx"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Vinculos
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimentos.id", ondelete="SET NULL"), index=True
    )
    canal_contratado_id: Mapped[int | None] = mapped_column(
        ForeignKey("canais_contratados.id", ondelete="SET NULL"), index=True
    )

    # Cliente = conta COMERCIAL (plano, limites), nao o tenant. Sobrou do
    # DDL original. E escrito por compatibilidade; query de tenant usa
    # SEMPRE empresa_id.
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), index=True
    )

    # Identificacao (nomes do banco)
    # SIP Call-ID. Chave de idempotencia: o PABX reenvia evento e o UNIQUE
    # impede bilhetar a mesma ligacao duas vezes.
    pabx_call_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    numero_origem: Mapped[str] = mapped_column(String(30), nullable=False)
    numero_destino: Mapped[str] = mapped_column(String(30), nullable=False)

    # Estado
    # O default espelha o DEFAULT do banco ("iniciando"). Se divergirem, o
    # Postgres grava o dele e a app procura um valor que nao existe.
    tipo: Mapped[str] = mapped_column(
        String(20), default=TipoChamada.ENTRADA.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=StatusChamada.INICIANDO.value, nullable=False, index=True
    )

    # Tempos
    iniciada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    atendida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracao_segundos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Gravacao - LGPD: audio e dado sensivel. Guardamos caminho e SHA-256.
    url_gravacao: Mapped[str | None] = mapped_column(String(500))
    gravacao_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # Resumo por IA no fim da chamada (DeepSeek). Existia no banco e tinha
    # sumido do model - quem analisava a ligacao lia NULL.
    resumo_ia: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    atendimento: Mapped["Atendimento | None"] = relationship(back_populates="chamadas")
    canal_contratado: Mapped["CanalContratado | None"] = relationship()


__all__ = ["ChamadaPABX"]
