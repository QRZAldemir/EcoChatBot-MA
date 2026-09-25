"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-Marcx · Webhook Exceptions
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     webhook_exceptions.py
@module   Backend / App / Exceptions
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define as exceções específicas do DOMÍNIO "WEBHOOK" do EcoChatBot-Marcx.

Um "webhook" é um endpoint HTTP que RECEBE notificações em tempo real
de plataformas externas (WhatsApp, Telegram, Discord, etc.). É o
mecanismo pelo qual o bot SABE que chegou uma nova mensagem.

FLUXO DO WEBHOOK
────────────────
    ┌────────────────────────────────────────────────────────────────┐
    │                                                                │
    │  1. Cliente envia mensagem no WhatsApp                         │
    │       │                                                        │
    │       ▼                                                        │
    │  2. WhatsApp dispara POST para o webhook do EcoChatBot         │
    │       │                                                        │
    │       ▼                                                        │
    │  3. FastAPI recebe em POST /api/webhook/{canal}                │
    │       │                                                        │
    │       ▼                                                        │
    │  4. WebhookService valida assinatura/token                     │
    │       │                                                        │
    │       ▼                                                        │
    │  5. WebhookService roteia para o handler correto               │
    │       │                                                        │
    │       ▼                                                        │
    │  6. BotService processa a mensagem                             │
    │                                                                │
    └────────────────────────────────────────────────────────────────┘

RELACIONAMENTO COM OUTROS OBJETOS DO PROJETO
────────────────────────────────────────────
    WebhookException (esta classe)
        │
        ├──► IntegracaoException         (do integracao_exceptions.py)
        │      • Cada integração pode exigir webhook
        │      • IntegracaoService configura o webhook no provedor
        │      • Se a integração falha → webhook não recebe eventos
        │
        ├──► CanalException              (do canal_exceptions.py)
        │      • Cada canal tem SEU webhook (/api/webhook/whatsapp,
        │        /api/webhook/telegram, etc.)
        │      • CanalWebhookException (canal) ≠ WebhookException (geral)
        │
        ├──► AuthException               (do auth_exceptions.py)
        │      • Webhooks exigem validação de assinatura/token
        │      • WebhookAssinaturaInvalidaException dispara quando
        │        o provedor envia webhook sem assinatura válida
        │
        ├──► TenantException             (do tenant_exceptions.py)
        │      • Cada webhook é roteado para 1 tenant
        │      • WebhookTenantNaoIdentificadoException dispara quando
        │        não é possível identificar o tenant
        │
        ├──► AtendimentoException        (do atendimento_exceptions.py)
        │      • Webhook recebe msg → cria/atualiza atendimento
        │      • AtendimentoJaEmAndamentoException pode ser disparada
        │        ao processar webhook de contato duplicado
        │
        └──► EcoChatBotException         (do base_exceptions.py)
               • Classe base de toda a hierarquia

EXCEÇÕES DISPONÍVEIS
────────────────────
    ┌──────────────────────────────────────────────┬─────────┬──────────────────┐
    │ Classe                                       │ Status  │ Quando usar      │
    ├──────────────────────────────────────────────┼─────────┼──────────────────┤
    │ WebhookException                             │ 500     │ Base             │
    │ WebhookNaoConfiguradoException               │ 422     │ Sem config       │
    │ WebhookInvalidoException                     │ 422     │ Payload inválido │
    │ WebhookAssinaturaInvalidaException           │ 401     │ Assinatura ruim  │
    │ WebhookNaoAutorizadoException                │ 403     │ IP não permitido │
    │ WebhookDuplicadoException                    │ 409     │ Evento duplicado │
    │ WebhookProcessamentoException                │ 500     │ Falha no process.│
    │ WebhookTenantNaoIdentificadoException        │ 400     │ Tenant ausente   │
    │ WebhookCanalNaoIdentificadoException         │ 400     │ Canal ausente    │
    └──────────────────────────────────────────────┴─────────┴──────────────────┘

⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
──────────────────────────────────────
Estas exceções servem a QUALQUER canal (WhatsApp, Telegram, Discord,
Facebook, Instagram, PABX) e a QUALQUER segmento de negócio.

USO
───
    from app.exceptions import WebhookAssinaturaInvalidaException

    if not validar_assinatura(request):
        raise WebhookAssinaturaInvalidaException(canal='WhatsApp')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import Optional

from app.exceptions.base_exceptions import EcoChatBotException


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÃO BASE DO DOMÍNIO "WEBHOOK"
# ═══════════════════════════════════════════════════════════════════════════


class WebhookException(EcoChatBotException):
    """
    Classe BASE para todas as exceções do domínio "webhook".

    Herda de `EcoChatBotException` (default status_code=500).

    Relacionamento:
        • Complementa `IntegracaoException` — a integração é a
          configuração, o webhook é o endpoint receptor.
        • Complementa `CanalException` — cada canal tem seu webhook.
    """

    def __init__(
        self,
        message: str = 'Erro de webhook',
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            detail=detail,
            error_code=error_code or 'WEBHOOK_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class WebhookNaoConfiguradoException(WebhookException):
    """
    O webhook NÃO FOI CONFIGURADO no provedor externo.

    HTTP Status: 422 Unprocessable Entity

    Relacionamento:
        • Complementa `IntegracaoNaoConfiguradaException` — a integração
          pode estar configurada mas o webhook não.
        • Disparada quando o admin do tenant tenta ativar um canal
          sem ter registrado a URL de webhook no provedor.

    Exemplo:
        raise WebhookNaoConfiguradoException(canal='WhatsApp')
    """

    def __init__(self, canal: Optional[str] = None) -> None:
        message = 'Webhook não configurado'
        if canal:
            message += f' para o canal: {canal}'

        super().__init__(
            message=message,
            status_code=422,
            error_code='WEBHOOK_NAO_CONFIGURADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE VALIDAÇÃO E AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════


class WebhookInvalidoException(WebhookException):
    """
    PAYLOAD do webhook está em formato INVÁLIDO.

    HTTP Status: 422 Unprocessable Entity

    Relacionamento:
        • Complementa `IntegracaoPayloadInvalidoException` (payload
          de SAÍDA) — este é payload de ENTRADA.
        • Disparada quando o JSON recebido não bate com o schema
          esperado do canal.

    Exemplo:
        raise WebhookInvalidoException(
            canal='Telegram',
            motivo='Campo "update_id" ausente'
        )
    """

    def __init__(self, canal: Optional[str] = None, motivo: Optional[str] = None) -> None:
        message = 'Payload do webhook inválido'
        if canal:
            message += f' ({canal})'
        if motivo:
            message += f': {motivo}'

        super().__init__(
            message=message,
            status_code=422,
            error_code='WEBHOOK_INVALIDO',
        )


class WebhookAssinaturaInvalidaException(WebhookException):
    """
    ASSINATURA do webhook é inválida (HMAC, X-Hub-Signature, etc.).

    HTTP Status: 401 Unauthorized

    Relacionamento:
        • WhatsApp e Facebook exigem validação via X-Hub-Signature-256.
        • Telegram não usa assinatura (usa secret token no path).
        • Disparada quando o HMAC não bate — indica possível ataque.

    ⚠️ SEGURANÇA: este evento DEVE ser logado em ferramenta de
    telemetria (Sentry, DataDog).

    Exemplo:
        raise WebhookAssinaturaInvalidaException(canal='WhatsApp')
    """

    def __init__(self, canal: Optional[str] = None) -> None:
        message = 'Assinatura do webhook inválida'
        if canal:
            message += f' ({canal})'

        super().__init__(
            message=message,
            status_code=401,
            error_code='WEBHOOK_ASSINATURA_INVALIDA',
        )


class WebhookNaoAutorizadoException(WebhookException):
    """
    A ORIGEM do webhook não está autorizada (IP, header, etc.).

    HTTP Status: 403 Forbidden

    Relacionamento:
        • Disparada quando o IP de origem não está na whitelist do
          provedor.
        • Complementa `AuthException.PermissaoNegadaException` (que é
          sobre o operador logado).

    Exemplo:
        raise WebhookNaoAutorizadoException(ip='1.2.3.4')
    """

    def __init__(self, ip: Optional[str] = None) -> None:
        message = 'Origem do webhook não autorizada'
        if ip:
            message += f' (IP: {ip})'

        super().__init__(
            message=message,
            status_code=403,
            error_code='WEBHOOK_NAO_AUTORIZADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE PROCESSAMENTO
# ═══════════════════════════════════════════════════════════════════════════


class WebhookDuplicadoException(WebhookException):
    """
    O EVENTO do webhook é DUPLICADO (já foi processado).

    HTTP Status: 409 Conflict

    Relacionamento:
        • Provedores como WhatsApp podem reenviar o mesmo evento.
        • O `WebhookService` usa Redis (`SETNX`) para idempotência.
        • Retornar 200 com "ignorado" é OK — mas logar.

    Exemplo:
        raise WebhookDuplicadoException(event_id='wamid.abc123')
    """

    def __init__(self, event_id: Optional[str] = None) -> None:
        message = 'Evento do webhook já foi processado'
        if event_id:
            message += f' (event_id: {event_id})'

        super().__init__(
            message=message,
            status_code=409,
            error_code='WEBHOOK_DUPLICADO',
        )


class WebhookProcessamentoException(WebhookException):
    """
    Falha no PROCESSAMENTO do webhook (após validação OK).

    HTTP Status: 500 Internal Server Error

    Relacionamento:
        • Disparada quando o `WebhookService` falha ao rotear a
          mensagem para o handler correto.
        • Pode escalar para `AtendimentoException` se o problema for
          no fluxo de atendimento.

    Exemplo:
        raise WebhookProcessamentoException(
            canal='WhatsApp',
            etapa='roteamento',
            motivo='Handler não encontrado'
        )
    """

    def __init__(
        self,
        canal: Optional[str] = None,
        etapa: Optional[str] = None,
        motivo: Optional[str] = None,
    ) -> None:
        message = 'Falha no processamento do webhook'
        if canal:
            message += f' ({canal})'
        if etapa:
            message += f' — etapa: {etapa}'
        if motivo:
            message += f'. {motivo}'

        super().__init__(
            message=message,
            status_code=500,
            error_code='WEBHOOK_PROCESSAMENTO_ERROR',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE IDENTIFICAÇÃO (TENANT / CANAL)
# ═══════════════════════════════════════════════════════════════════════════


class WebhookTenantNaoIdentificadoException(WebhookException):
    """
    Não foi possível IDENTIFICAR O TENANT do webhook.

    HTTP Status: 400 Bad Request

    Relacionamento:
        • Complementa `TenantException.TenantAusenteException` (que é
          sobre requisições HTTP do operador).
        • Aqui o tenant é inferido pelo número de destino (WhatsApp)
          ou pelo `bot_token` (Telegram).

    Exemplo:
        raise WebhookTenantNaoIdentificadoException(
            canal='WhatsApp',
            destino='67-3416-7800'
        )
    """

    def __init__(self, canal: Optional[str] = None, destino: Optional[str] = None) -> None:
        message = 'Tenant não identificado no webhook'
        if canal:
            message += f' ({canal})'
        if destino:
            message += f' — destino: {destino}'

        super().__init__(
            message=message,
            status_code=400,
            error_code='WEBHOOK_TENANT_NAO_IDENTIFICADO',
        )


class WebhookCanalNaoIdentificadoException(WebhookException):
    """
    Não foi possível IDENTIFICAR O CANAL do webhook.

    HTTP Status: 400 Bad Request

    Relacionamento:
        • Complementa `CanalException.CanalNaoEncontradoException`.
        • Aqui o canal é inferido pelo path da URL
          (/api/webhook/whatsapp, /api/webhook/telegram).

    Exemplo:
        raise WebhookCanalNaoIdentificadoException(url='/api/webhook/xyz')
    """

    def __init__(self, url: Optional[str] = None) -> None:
        message = 'Canal não identificado no webhook'
        if url:
            message += f' — URL: {url}'

        super().__init__(
            message=message,
            status_code=400,
            error_code='WEBHOOK_CANAL_NAO_IDENTIFICADO',
        )


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'WebhookException',
    'WebhookNaoConfiguradoException',
    'WebhookInvalidoException',
    'WebhookAssinaturaInvalidaException',
    'WebhookNaoAutorizadoException',
    'WebhookDuplicadoException',
    'WebhookProcessamentoException',
    'WebhookTenantNaoIdentificadoException',
    'WebhookCanalNaoIdentificadoException',
]