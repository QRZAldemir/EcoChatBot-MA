"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Models · UsuarioCanal
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     usuario_canal_models.py
@module   Backend / app/models
@author   Aldemir Queiroz
@since    2026
@version  0.1.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Tabela de junção entre o atendente (`Usuario`) e o canal contratado
(`CanalContratado`). É ela que decide, por dado, se a pessoa atende um
canal só ou vários.

O QUE ESTE ARQUIVO É
───────────────────
A tabela que materializa a decisão do gestor. Um atendente restrito a um
canal tem um vínculo; um atendente multicanal tem vários. A mesma estrutura
serve os dois casos — não existe "tabela de canal único" e "tabela de canal
vários", e é por isso que a pergunta "atende um ou vários?" tem resposta
simples: quantos vínculos existem.

O OBJETO
────────
    UsuarioCanal — tabela `usuarios_canais`, herda `TimestampMixin` e `Base`:
        id                    Integer, PK, indexada
        usuario_id            FK usuarios.id, ON DELETE CASCADE, obrigatório
        canal_contratado_id   FK canais_contratados.id, ON DELETE CASCADE,
                             obrigatório
        principal             Boolean, default=False — por qual canal o
                             atendente é notificado primeiro
        ativo                 Boolean, default=True — desativa o vínculo sem
                             apagar o histórico
        usuario               relationship(back_populates="vinculos_canal")
        canal_contratado      relationship(back_populates="vinculos_usuario")
    UniqueConstraint `uq_usuarios_canais_vinculo` sobre
    (usuario_id, canal_contratado_id): um usuário não pode ter dois vínculos
    para o mesmo canal.

EXEMPLO DE DADOS
────────────────
    Ana atende só WhatsApp:
        Vinculo(Ana, Canal(whatsapp), principal=True)
    Bruno atende WhatsApp, Telegram e PABX:
        Vinculo(Bruno, Canal(whatsapp), principal=True)
        Vinculo(Bruno, Canal(telegram), principal=False)
        Vinculo(Bruno, Canal(pabx),    principal=False)

POR QUE `principal` NÃO GANHOU RESTRIÇÃO NO BANCO
────────────────────────────────────────────────
"Ao máximo um principal por usuário" é regra de negócio, e o banco não sabe
o que é principal sem essa regra. Fica no service. No banco, `principal` é
apenas uma flag que o gestor preencheu.

POR QUE OS DOIS `ondelete` SÃO CASCADE
─────────────────────────────────────
Apagar o atendente ou cancelar o canal contratado tem que levar os vínculos
junto: vínculo sem usuário nem canal é lixo. O histórico que NÃO pode sumir é
o outro — `Atendimento` guarda o que aconteceu e não é apagado por aqui.

POR QUE `ativo` E NÃO SÓ APAGAR
──────────────────────────────
`ativo=False` tira a pessoa da fila daquele canal imediatamente, sem
destruir o passado: os atendimentos já registrados continuam apontando para
o mesmo vínculo, e o relatório continua fechando.

RELACIONAMENTO
──────────────
    Usuario (1) ── (N) UsuarioCanal ── (1) CanalContratado (1) ── (N) Telefone
    UsuarioCanal ── origina ──> Atendimento
    reexportado por app/models/__init__.py
    referenciado em app/models/usuario_models.py e app/models/canal_models.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.canal_models import CanalContratado
    from app.models.usuario_models import Usuario


class UsuarioCanal(TimestampMixin, Base):
    """Vínculo de um atendente com um canal contratado."""

    __tablename__ = "usuarios_canais"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "canal_contratado_id", name="uq_usuarios_canais_vinculo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    canal_contratado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("canais_contratados.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    principal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="vinculos_canal")
    canal_contratado: Mapped["CanalContratado"] = relationship(
        back_populates="vinculos_usuario"
    )


