"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Token Revogado (Blacklist JWT)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     token_revogado_models.py
@module   Backend / App / Models / Token Revogado
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Blacklist de JWT revogados antes da expiração natural. JWT é stateless
por definição — a única forma de invalidar um token antes do vencimento
é manter uma lista de bloqueio.

CASOS DE USO
────────────
    • Logout explícito do usuário
    • Troca de senha (todos os tokens antigos morrem)
    • Detecção de uso suspeito (roubo de token)
    • Rotação de chave de assinatura
    • Bloqueio administrativo

RELACIONAMENTO
──────────────
    Usuario (1) ── (N) TokenRevogado
    (não herda TenantMixin: o token pode existir antes do login completo)

ESTRATÉGIA
──────────
    • Tabela em PostgreSQL (fonte da verdade — auditoria)
    • Redis (cache de leitura rápida no middleware de auth)
    • Rotina de limpeza: remove registros com `expira_em < now()`
      (o token já é inválido naturalmente)

SEGURANÇA
─────────
    • Armazenar o HASH do token (SHA-256), NUNCA o token cru
    • `jti` (JWT ID) é o identificador único do token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import MotivoRevogacao
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa_models import Usuario


class TokenRevogado(TimestampMixin, Base):
    """
    Registro de JWT revogado antes da expiração natural.

    O `jti` é o índice primário de busca no middleware de autenticação:
        SELECT 1 FROM tokens_revogados WHERE jti = :jti
    """

    __tablename__ = "tokens_revogados"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    # ─── Identificação do token ───────────────────────────────────────────
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # JWT ID (claim "jti")
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # SHA-256 do token completo (auditoria)

    # ─── Motivo ───────────────────────────────────────────────────────────
    motivo: Mapped[str] = mapped_column(
        String(20), default=MotivoRevogacao.LOGOUT.value, nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    # ─── Ciclo de vida ────────────────────────────────────────────────────
    expira_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # quando o token expiraria naturalmente — usado pelo expurgo

    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_origem: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(300))

    # ─── Relacionamentos ──────────────────────────────────────────────────
    usuario: Mapped["Usuario | None"] = relationship()


__all__ = ["TokenRevogado"]