"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Atendimento Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "ATENDIMENTO" do
EcoChatBot-Marcx.

DOMÍNIO "ATENDIMENTO"
─────────────────────
Um "atendimento" é uma conversa entre um contato (cliente) e um
operador (atendente) em um canal (WhatsApp, Telegram, etc.).

Estados possíveis:
    • aguardando  → na fila
    • em_atendimento → em conversa
    • transferido → passado para outro atendente/depto
    • encerrado   → finalizado
    • abandonado  → contato saiu sem finalizar

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────────────┬─────────┬──────────────────┐
    │ Classe                                       │ Status  │ Quando usar      │
    ├──────────────────────────────────────────────┼─────────┼──────────────────┤
    │ AtendimentoException                         │ 500     │ Base             │
    │ AtendimentoNaoEncontradoException            │ 404     │ Não existe       │
    │ AtendimentoJaEncerradoException              │ 409     │ Já finalizado    │
    │ AtendimentoNaoTransferivelException          │ 409     │ Não pode transfer│
    │ AtendimentoSemAtendenteException             │ 422     │ Sem atendente    │
    │ AtendimentoJaEmAndamentoException            │ 409     │ Duplicado        │
    │ FilaCheiaException                           │ 503     │ Fila lotada      │
    └──────────────────────────────────────────────┴─────────┴──────────────────┘

USO
───
    from app.exceptions import AtendimentoNaoEncontradoException

    if not atendimento:
        raise AtendimentoNaoEncontradoException(atendimento_id=42)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


class AtendimentoException(EcoChatBotException):
    """Classe BASE para todas as exceções do domínio "atendimento"."""

    def __init__(
        self,
        message: str = 'Erro relacionado ao atendimento',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'ATENDIMENTO_ERROR',
        )


class AtendimentoNaoEncontradoException(AtendimentoException):
    """ATENDIMENTO NÃO ENCONTRADO. HTTP Status: 404"""

    def __init__(self, atendimento_id: Optional[int] = None) -> None:
        message = 'Atendimento não encontrado'
        if atendimento_id:
            message += f' (id={atendimento_id})'

        super().__init__(
            message=message,
            status_code=404,
            error_code='ATENDIMENTO_NAO_ENCONTRADO',
        )


class AtendimentoJaEncerradoException(AtendimentoException):
    """ATENDIMENTO JÁ ENCERRADO. HTTP Status: 409"""

    def __init__(self, atendimento_id: Optional[int] = None) -> None:
        message = 'Atendimento já encerrado'
        if atendimento_id:
            message += f' (id={atendimento_id})'

        super().__init__(
            message=message,
            status_code=409,
            error_code='ATENDIMENTO_JA_ENCERRADO',
        )


class AtendimentoJaEmAndamentoException(AtendimentoException):
    """ATENDIMENTO JÁ EM ANDAMENTO. HTTP Status: 409"""

    def __init__(self, contato_id: Optional[int] = None) -> None:
        message = 'Já existe um atendimento em andamento para este contato'
        if contato_id:
            message += f' (contato_id={contato_id})'

        super().__init__(
            message=message,
            status_code=409,
            error_code='ATENDIMENTO_JA_EM_ANDAMENTO',
        )


class AtendimentoNaoTransferivelException(AtendimentoException):
    """ATENDIMENTO NÃO PODE SER TRANSFERIDO. HTTP Status: 409"""

    def __init__(self, motivo: Optional[str] = None) -> None:
        message = 'Atendimento não pode ser transferido'
        if motivo:
            message += f': {motivo}'

        super().__init__(
            message=message,
            status_code=409,
            error_code='ATENDIMENTO_NAO_TRANSFERIVEL',
        )


class AtendimentoSemAtendenteException(AtendimentoException):
    """ATENDIMENTO SEM ATENDENTE ATRIBUÍDO. HTTP Status: 422"""

    def __init__(self, atendimento_id: Optional[int] = None) -> None:
        message = 'Atendimento sem atendente atribuído'
        if atendimento_id:
            message += f' (id={atendimento_id})'

        super().__init__(
            message=message,
            status_code=422,
            error_code='ATENDIMENTO_SEM_ATENDENTE',
        )


class FilaCheiaException(AtendimentoException):
    """FILA DE ATENDIMENTO CHEIA. HTTP Status: 503"""

    def __init__(self, departamento: Optional[str] = None, limite: Optional[int] = None) -> None:
        message = 'Fila de atendimento cheia'
        if departamento:
            message += f' para o departamento: {departamento}'
        if limite:
            message += f' (limite: {limite})'

        super().__init__(
            message=message,
            status_code=503,
            error_code='FILA_CHEIA',
        )


__all__ = [
    'AtendimentoException',
    'AtendimentoNaoEncontradoException',
    'AtendimentoJaEncerradoException',
    'AtendimentoJaEmAndamentoException',
    'AtendimentoNaoTransferivelException',
    'AtendimentoSemAtendenteException',
    'FilaCheiaException',
]