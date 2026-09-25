"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · IA Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     ia_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "IA" (Inteligência Artificial)
e "ACESSIBILIDADE" (OCR + TTS) do EcoChatBot-Marcx.

DOMÍNIO "IA"
────────────
A IA do EcoChatBot-Marcx usa:
    • DeepSeek     → LLM (conversas)
    • OCR          → Tesseract (imagem → texto) — acessibilidade
    • TTS          → gTTS / Edge-TTS (texto → voz) — acessibilidade

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────────┬─────────┬──────────────────┐
    │ Classe                                   │ Status  │ Quando usar      │
    ├──────────────────────────────────────────┼─────────┼──────────────────┤
    │ IAException                              │ 500     │ Base             │
    │ DeepSeekException                        │ 502     │ Erro na LLM      │
    │ IAIndisponivelException                  │ 503     │ LLM offline      │
    │ IARespostaInvalidaException              │ 502     │ Resposta malform.│
    │ IATokenExcedidoException                 │ 413     │ Prompt muito gr. │
    │ OCRException                             │ 500     │ Erro no OCR      │
    │ OCRImagemInvalidaException               │ 422     │ Imagem inválida  │
    │ OCRNenhumTextoException                  │ 422     │ Sem texto        │
    │ TTSException                             │ 500     │ Erro no TTS      │
    │ TTSVozNaoSuportadaException              │ 422     │ Voz indisponível │
    └──────────────────────────────────────────┴─────────┴──────────────────┘

⚠️ ESCOPO DE ACESSIBILIDADE
───────────────────────────
OCR + TTS são os recursos de ACESSIBILIDADE do projeto, voltados para:
    • 👴 Idosos (não digitam — enviam foto)
    • 📖 Analfabetos funcionais (não leem — ouvem)
    • 👁️ Deficientes visuais (combinam OCR + TTS)
    • 🧠 Deficientes cognitivos (interface simplificada)
    • 📱 Baixa alfabetização digital (print de qualquer coisa)

USO
───
    from app.exceptions import DeepSeekException, OCRException

    try:
        resposta = await deepseek.chat(mensagens)
    except Exception as e:
        raise DeepSeekException(str(e))

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "IA"
# ═══════════════════════════════════════════════════════════════════════════


class IAException(EcoChatBotException):
    """Classe BASE para todas as exceções do domínio "IA"."""

    def __init__(
        self,
        message: str = 'Erro relacionado à IA',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'IA_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE LLM (DeepSeek)
# ═══════════════════════════════════════════════════════════════════════════


class DeepSeekException(IAException):
    """Erro genérico da IA DeepSeek. HTTP Status: 502"""

    def __init__(self, message: str = 'Erro na comunicação com DeepSeek') -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code='DEEPSEEK_ERROR',
        )


class IAIndisponivelException(IAException):
    """IA INDISPONÍVEL (offline ou timeout). HTTP Status: 503"""

    def __init__(self, provedor: Optional[str] = None) -> None:
        message = 'Serviço de IA indisponível'
        if provedor:
            message += f' ({provedor})'

        super().__init__(
            message=message,
            status_code=503,
            error_code='IA_INDISPONIVEL',
        )


class IARespostaInvalidaException(IAException):
    """RESPOSTA DA IA MALFORMADA. HTTP Status: 502"""

    def __init__(self, motivo: Optional[str] = None) -> None:
        message = 'Resposta da IA em formato inválido'
        if motivo:
            message += f': {motivo}'

        super().__init__(
            message=message,
            status_code=502,
            error_code='IA_RESPOSTA_INVALIDA',
        )


class IATokenExcedidoException(IAException):
    """PROMPT EXCEDEU O LIMITE DE TOKENS. HTTP Status: 413"""

    def __init__(self, tokens: Optional[int] = None, limite: Optional[int] = None) -> None:
        message = 'Prompt excedeu o limite de tokens'
        if tokens and limite:
            message += f' ({tokens}/{limite})'

        super().__init__(
            message=message,
            status_code=413,
            error_code='IA_TOKEN_EXCEDIDO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE OCR (ACESSIBILIDADE)
# ═══════════════════════════════════════════════════════════════════════════


class OCRException(IAException):
    """Erro genérico de OCR. HTTP Status: 500"""

    def __init__(self, message: str = 'Erro no processamento OCR') -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code='OCR_ERROR',
        )


class OCRImagemInvalidaException(OCRException):
    """IMAGEM INVÁLIDA para OCR. HTTP Status: 422"""

    def __init__(self, motivo: Optional[str] = None) -> None:
        message = 'Imagem inválida para OCR'
        if motivo:
            message += f': {motivo}'

        super().__init__(message=message)
        self.status_code = 422
        self.error_code = 'OCR_IMAGEM_INVALIDA'


class OCRNenhumTextoException(OCRException):
    """NENHUM TEXTO ENCONTRADO na imagem. HTTP Status: 422"""

    def __init__(self) -> None:
        super().__init__(message='Nenhum texto encontrado na imagem')
        self.status_code = 422
        self.error_code = 'OCR_NENHUM_TEXTO'


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE TTS (ACESSIBILIDADE)
# ═══════════════════════════════════════════════════════════════════════════


class TTSException(IAException):
    """Erro genérico de TTS (texto → voz). HTTP Status: 500"""

    def __init__(self, message: str = 'Erro na síntese de voz (TTS)') -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code='TTS_ERROR',
        )


class TTSVozNaoSuportadaException(TTSException):
    """VOZ NÃO SUPORTADA para o idioma. HTTP Status: 422"""

    def __init__(self, idioma: Optional[str] = None) -> None:
        message = 'Voz não suportada'
        if idioma:
            message += f' para o idioma: {idioma}'

        super().__init__(message=message)
        self.status_code = 422
        self.error_code = 'TTS_VOZ_NAO_SUPORTADA'


__all__ = [
    'IAException',
    'DeepSeekException',
    'IAIndisponivelException',
    'IARespostaInvalidaException',
    'IATokenExcedidoException',
    'OCRException',
    'OCRImagemInvalidaException',
    'OCRNenhumTextoException',
    'TTSException',
    'TTSVozNaoSuportadaException',
]