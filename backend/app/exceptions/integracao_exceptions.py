"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Integração Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     integracao_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "INTEGRAÇÃO" do
EcoChatBot-MA — erros de comunicação com plataformas externas
de atendimento.

Todas as classes herdam de `IntegracaoException`, que por sua vez herda
de `EcoChatBotException`, garantindo:

    • status_code HTTP
    • error_code programático
    • detail para resposta JSON
    • método to_dict() para serialização

DOMÍNIO "INTEGRAÇÃO"
────────────────────
Uma "integração" é o canal de comunicação entre o EcoChatBot-MA
e uma plataforma externa (WhatsApp Business API, Telegram Bot API,
Discord API, Facebook Messenger, Instagram Direct, MicroSIP/PABX).

┌──────────────────────────────────────────────────────────────────────┐
│  CANAIS SUPORTADOS                                                   │
├──────────────────────────────────────────────────────────────────────┤
│  • 💬 WhatsApp Business API    →  graph.facebook.com/v20.0          │
│  • ✈️ Telegram Bot API         →  api.telegram.org                  │
│  • 🎮 Discord Bot API          →  discord.com/api/v10               │
│  • 📘 Facebook Messenger       →  graph.facebook.com/v20.0          │
│  • 📷 Instagram Direct         →  graph.facebook.com/v20.0          │
│  • ☎️ MicroSIP / PABX / VoIP   →  protocolo SIP (sip.js)            │
│  • 👁️ OCR (Tesseract)          →  acessibilidade                    │
│  • 🔊 TTS (gTTS / Edge-TTS)    →  acessibilidade                    │
└──────────────────────────────────────────────────────────────────────┘

RELACIONAMENTO COM OUTROS OBJETOS DO PROJETO
────────────────────────────────────────────
    IntegracaoException (esta classe)
        │
        ├──► CanalException              (do canal_exceptions.py)
        │      • Canal está vinculado a 1+ integração
        │      • Se a integração falha → canal fica "desconectado"
        │      • CanalDesconectadoException pode ser disparada quando
        │        a integração retorna erro persistente
        │
        ├──► WebhookException            (do webhook_exceptions.py)
        │      • Cada integração pode exigir webhook
        │      • Se webhook falha na config → integração não recebe msgs
        │      • WebhookNaoConfiguradoException pode bloquear a integração
        │
        ├──► IAException                 (do ia_exceptions.py)
        │      • OCR e TTS são integrações internas de IA
        │      • IAIndisponivelException pode ser disparada quando
        │        o provedor externo de IA está offline
        │
        ├──► AuthException               (do auth_exceptions.py)
        │      • Toda integração exige autenticação (token/API key)
        │      • TokenExpiradoException pode ser disparada quando o
        │        token da integração expira
        │
        ├──► TenantException             (do tenant_exceptions.py)
        │      • Cada integração pertence a 1 tenant (empresa)
        │      • TenantAcessoNegadoException pode ser disparada quando
        │        um tenant tenta usar integração de outro
        │
        └──► EcoChatBotException         (do base_exceptions.py)
               • Classe base de toda a hierarquia

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────────────┬─────────┬──────────────────┐
    │ Classe                                       │ Status  │ Quando usar      │
    ├──────────────────────────────────────────────┼─────────┼──────────────────┤
    │ IntegracaoException                          │ 500     │ Base             │
    │ IntegracaoNaoConfiguradaException            │ 422     │ Sem config       │
    │ IntegracaoDesabilitadaException              │ 503     │ Desabilitada     │
    │ IntegracaoIndisponivelException              │ 503     │ Offline          │
    │ IntegracaoTokenInvalidoException             │ 401     │ Token inválido   │
    │ IntegracaoTimeoutException                   │ 504     │ Timeout          │
    │ IntegracaoRateLimitException                 │ 429     │ Rate limit       │
    │ IntegracaoPayloadInvalidoException           │ 422     │ Payload errado   │
    │ IntegracaoRespostaInvalidaException          │ 502     │ Resposta inválida│
    │ IntegracaoNaoSuportadaException              │ 501     │ Não implementada │
    └──────────────────────────────────────────────┴─────────┴──────────────────┘

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções servem a QUALQUER canal e segmento de negócio.

USO
───
    from app.exceptions import IntegracaoIndisponivelException

    try:
        response = await whatsapp.send(payload)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            raise IntegracaoIndisponivelException(canal='WhatsApp')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "INTEGRAÇÃO"
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoException(EcoChatBotException):
    """
    Classe BASE para todas as exceções do domínio "integração".

    Herda de `EcoChatBotException` (default status_code=500).

    Relacionamento:
        • Complementa `CanalException` — o canal é a entidade, a
          integração é o mecanismo de comunicação.
        • Complementa `WebhookException` — a integração pode exigir
          webhook para receber mensagens.
    """

    def __init__(
        self,
        message: str = 'Erro de integração',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'INTEGRACAO_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoNaoConfiguradaException(IntegracaoException):
    """
    A integração NÃO FOI CONFIGURADA (faltam credenciais, tokens, etc.).

    HTTP Status: 422 Unprocessable Entity

    Relacionamento:
        • Disparada pelo `IntegracaoService` ao tentar usar uma
          integração sem as variáveis de ambiente obrigatórias.
        • Impede que `CanalService` ative o canal correspondente.

    Exemplo:
        raise IntegracaoNaoConfiguradaException(canal='WhatsApp')
    """

    def __init__(self, canal: Optional[str] = None) -> None:
        message = 'Integração não configurada'
        if canal:
            message += f' para o canal: {canal}'

        super().__init__(
            message=message,
            status_code=422,
            error_code='INTEGRACAO_NAO_CONFIGURADA',
        )


class IntegracaoDesabilitadaException(IntegracaoException):
    """
    A integração está DESABILITADA nas configurações do tenant.

    HTTP Status: 503 Service Unavailable

    Relacionamento:
        • Verificada antes de qualquer tentativa de envio.
        • Uma `CanalException` pode ser disparada se o canal estiver
          vinculado a uma integração desabilitada.

    Exemplo:
        raise IntegracaoDesabilitadaException(canal='Telegram')
    """

    def __init__(self, canal: Optional[str] = None) -> None:
        message = 'Integração desabilitada'
        if canal:
            message += f' para o canal: {canal}'

        super().__init__(
            message=message,
            status_code=503,
            error_code='INTEGRACAO_DESABILITADA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE COMUNICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoIndisponivelException(IntegracaoException):
    """
    A integração está INDISPONÍVEL (servidor externo offline).

    HTTP Status: 503 Service Unavailable

    Relacionamento:
        • Disparada quando o provedor externo retorna 5xx.
        • Pode escalar para `CanalDesconectadoException` se persistir.

    Exemplo:
        raise IntegracaoIndisponivelException(canal='WhatsApp')
    """

    def __init__(self, canal: Optional[str] = None, status_externo: Optional[int] = None) -> None:
        message = 'Integração indisponível'
        if canal:
            message += f' ({canal})'
        if status_externo:
            message += f' — servidor externo retornou {status_externo}'

        super().__init__(
            message=message,
            status_code=503,
            error_code='INTEGRACAO_INDISPONIVEL',
        )


class IntegracaoTimeoutException(IntegracaoException):
    """
    TIMEOUT na comunicação com a integração externa.

    HTTP Status: 504 Gateway Timeout

    Relacionamento:
        • Disparada quando o provedor demora além do limite.
        • Deve disparar retry automático no `IntegracaoService`.

    Exemplo:
        raise IntegracaoTimeoutException(canal='Telegram', timeout_ms=5000)
    """

    def __init__(self, canal: Optional[str] = None, timeout_ms: Optional[int] = None) -> None:
        message = 'Timeout na integração'
        if canal:
            message += f' ({canal})'
        if timeout_ms:
            message += f' após {timeout_ms}ms'

        super().__init__(
            message=message,
            status_code=504,
            error_code='INTEGRACAO_TIMEOUT',
        )


class IntegracaoRateLimitException(IntegracaoException):
    """
    RATE LIMIT atingido no provedor externo.

    HTTP Status: 429 Too Many Requests

    Relacionamento:
        • Provedores como WhatsApp/Telegram limitam requisições.
        • Dispara backoff exponencial no `IntegracaoService`.
        • Se persistir, escalar para `IntegracaoIndisponivelException`.

    Exemplo:
        raise IntegracaoRateLimitException(canal='WhatsApp', retry_after=60)
    """

    def __init__(self, canal: Optional[str] = None, retry_after: Optional[int] = None) -> None:
        message = 'Rate limit atingido na integração'
        if canal:
            message += f' ({canal})'
        if retry_after:
            message += f'. Tentar novamente em {retry_after}s'

        super().__init__(
            message=message,
            status_code=429,
            error_code='INTEGRACAO_RATE_LIMIT',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE AUTENTICAÇÃO DA INTEGRAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoTokenInvalidoException(IntegracaoException):
    """
    TOKEN/API KEY da integração é inválido ou expirado.

    HTTP Status: 401 Unauthorized

    Relacionamento:
        • Diferente de `AuthException.TokenExpiradoException` (que é
          sobre o JWT do operador) — este é sobre o token DA INTEGRAÇÃO.
        • Disparado pelo `IntegracaoService` ao receber 401 do provedor.
        • Deve alertar o admin do tenant para reconfigurar.

    Exemplo:
        raise IntegracaoTokenInvalidoException(canal='WhatsApp')
    """

    def __init__(self, canal: Optional[str] = None, provedor: Optional[str] = None) -> None:
        message = 'Token da integração inválido ou expirado'
        if canal:
            message += f' ({canal})'
        if provedor:
            message += f' — reconfigurar no {provedor}'

        super().__init__(
            message=message,
            status_code=401,
            error_code='INTEGRACAO_TOKEN_INVALIDO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE PAYLOAD / RESPOSTA
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoPayloadInvalidoException(IntegracaoException):
    """
    PAYLOAD enviado à integração está em formato inválido.

    HTTP Status: 422 Unprocessable Entity

    Relacionamento:
        • Disparado quando o `MensagemService` monta um payload
          incompatível com o formato do canal.
        • Complementa `ValidationException` (que é genérico).

    Exemplo:
        raise IntegracaoPayloadInvalidoException(
            canal='WhatsApp',
            motivo='Campo "to" obrigatório'
        )
    """

    def __init__(self, canal: Optional[str] = None, motivo: Optional[str] = None) -> None:
        message = 'Payload inválido para a integração'
        if canal:
            message += f' ({canal})'
        if motivo:
            message += f': {motivo}'

        super().__init__(
            message=message,
            status_code=422,
            error_code='INTEGRACAO_PAYLOAD_INVALIDO',
        )


class IntegracaoRespostaInvalidaException(IntegracaoException):
    """
    RESPOSTA da integração está em formato inesperado.

    HTTP Status: 502 Bad Gateway

    Relacionamento:
        • Disparado quando o provedor retorna 200 mas o JSON não
          bate com o schema esperado.
        • Complementa `IARespostaInvalidaException` (que é sobre IA).

    Exemplo:
        raise IntegracaoRespostaInvalidaException(
            canal='Telegram',
            motivo='Campo "result" ausente'
        )
    """

    def __init__(self, canal: Optional[str] = None, motivo: Optional[str] = None) -> None:
        message = 'Resposta inválida da integração'
        if canal:
            message += f' ({canal})'
        if motivo:
            message += f': {motivo}'

        super().__init__(
            message=message,
            status_code=502,
            error_code='INTEGRACAO_RESPOSTA_INVALIDA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE SUPORTE
# ═══════════════════════════════════════════════════════════════════════════


class IntegracaoNaoSuportadaException(IntegracaoException):
    """
    Tipo de integração NÃO É SUPORTADO pela aplicação.

    HTTP Status: 501 Not Implemented

    Relacionamento:
        • Complementa `CanalNaoSuportadoException` — o canal é o
          ponto de vista do usuário; a integração é o ponto de vista
          técnico.

    Exemplo:
        raise IntegracaoNaoSuportadaException(tipo='skype')
    """

    def __init__(self, tipo: Optional[str] = None) -> None:
        message = 'Integração não suportada'
        if tipo:
            message += f': {tipo}'

        super().__init__(
            message=message,
            status_code=501,
            error_code='INTEGRACAO_NAO_SUPORTADA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'IntegracaoException',
    'IntegracaoNaoConfiguradaException',
    'IntegracaoDesabilitadaException',
    'IntegracaoIndisponivelException',
    'IntegracaoTimeoutException',
    'IntegracaoRateLimitException',
    'IntegracaoTokenInvalidoException',
    'IntegracaoPayloadInvalidoException',
    'IntegracaoRespostaInvalidaException',
    'IntegracaoNaoSuportadaException',
]