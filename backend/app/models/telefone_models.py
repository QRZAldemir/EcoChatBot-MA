"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Telefone da Empresa
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     telefone_models.py
@module   Backend / App / Models / Telefone
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Entidade do NÚMERO DE TELEFONE da Empresa. É o eixo da contratação: o
telefone é o que a empresa usa para atender, e cada canal contratado
pertence a um telefone.

ANTES (errado)
──────────────
O telefone era apenas `empresa.telefone` — uma String(20) solta, sem
identidade própria. `canais_contratados` guardava o número dentro de
`credenciais` (JSON em TEXT), onde o banco não o enxerga. Resultado: a
unicidade era `UNIQUE (empresa_id, tipo)`, que IMPEDIA a empresa de
contratar um 2º WhatsApp mesmo tendo um 2º número.

AGORA (correto)
──────────────
O telefone é uma entidade. A unicidade do canal passa a ser
`UNIQUE (telefone_id, tipo)`.

EXEMPLO PRÁTICO
───────────────
    Empresa: Aldemir Ltda
    ├── Telefone(numero="556734167800", principal=True)
    │     ├── CanalContratado(tipo="whatsapp")   ✅  1 whatsapp
    │     ├── CanalContratado(tipo="telegram")   ✅  1 telegram
    │     └── CanalContratado(tipo="pabx")       ✅  1 pabx
    └── Telefone(numero="5567992469894")
          └── CanalContratado(tipo="whatsapp")   ✅  2º whatsapp (outro número)

RELACIONAMENTO
──────────────
    Cliente (1) ── (N) Telefone
    Empresa  (1) ── (N) Telefone ── (N) CanalContratado
                                       │
                                       ├── (N) Conexao        (status/histórico do socket)
                                       ├── (N) Atendimento    (mensagens recebidas)
                                       └── (N) Menu           (menu do canal)

REGRAS DE NEGÓCIO
─────────────────
    • Unicidade: `UNIQUE (empresa_id, numero)` — o mesmo número não é
      cadastrado duas vezes na mesma Empresa
    • Cada telefone comporta 1 canal de cada tipo: `UNIQUE (telefone_id, tipo)`
      em `canais_contratados`
    • O mesmo telefone PODE atender canais de tipos diferentes
    • `principal=True` marca o número principal (o da Empresa)
    • Formato E.164 sem separadores: "556734167800"
    • Soft delete: desativar um telefone NÃO apaga o histórico de
      atendimentos dos canais nele
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_models import CanalContratado
    from app.models.empresa_models import Empresa


class Telefone(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Telefone da Empresa — base sobre a qual os canais são contratados.

    Este model é a FONTE DA VERDADE do número. `empresa.telefone` e
    `usuario.telefone` continuam existindo como dados de contato, mas quem
    vale para fins de CONTRATAÇÃO é esta tabela.
    """

    __tablename__ = "telefones"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "numero",
            name="uq_telefones_empresa_numero",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Dono do número ───────────────────────────────────────────────────

    # ─── O número ─────────────────────────────────────────────────────────
    numero: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="E.164 sem separadores — ex.: 556734167800",
    )
    pais: Mapped[str] = mapped_column(
        String(4), nullable=False, default="55",
        comment="Código do país ISO — 55 = Brasil",
    )

    # ─── Identificação ────────────────────────────────────────────────────
    descricao: Mapped[str | None] = mapped_column(
        String(80), comment='ex.: "Principal", "Loja Centro"'
    )
    principal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Telefone principal da Empresa",
    )

    # ─── Controle ─────────────────────────────────────────────────────────
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relacionamentos ──────────────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="telefones")
    canais: Mapped[List["CanalContratado"]] = relationship(
        back_populates="telefone", cascade="all, delete-orphan"
    )


__all__ = ["Telefone"]
