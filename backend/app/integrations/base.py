# ==============================================================================
# ARQUIVO.....: base.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Interface Base para Adaptadores de Canais de Comunicação
# VERSÃO......: 2.0.0 (Refatorado de channels.base para canais.base - LSP)
# CRIADO EM...: 2026-10-07
# ATUALIZADO..: 2026-10-09
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: FastAPI / Protocol (Structural Subtyping)
# ==============================================================================
# DESCRIÇÃO...:
# Define o contrato (interface) abstrato para todos os adaptadores de canais
# de comunicação (WhatsApp, Telegram, PABX, etc.).
#
# FUNCIONALIDADE:
#   - Estabelece o protocolo obrigatório para envio de mensagens.
#   - Garante o Princípio da Substituição de Liskov (LSP): o BotService trata
#     todos os canais de forma idêntica, independente do provedor subjacente.
#   - Documenta o contrato de exceções: adaptadores DEVEM levantar apenas
#     subclasses de CanalIntegracaoError (definidas em canal_exceptions.py).
#
# DECISÕES DE ARQUITETURA:
#   - Usa Protocol (PEP 544) em vez de ABC para permitir duck typing.
#   - Todos os métodos são assíncronos (async def) para não bloquear o Event Loop.
#   - O contrato de exceções é documentado via docstring (Raises).
#
# RELACIONAMENTOS:
#   - Implementado por: app.canais.whatsapp_integration.WhatsAppEvolutionAdapter
#   - Implementado por: app.canais.telegram_integration.TelegramBotAdapter
#   - Implementado por: app.canais.pabx_integration.PABXSIPAdapter (futuro)
#   - Consumido por: app.services.bot_service.BotService
#   - Exceções: app.exceptions.canal_exceptions.CanalIntegracaoError (e subclasses)
# ==============================================================================
"""
Interface base para adaptadores de canais de comunicação.

Define o contrato que TODOS os adaptadores devem cumprir para serem
registrados na Factory e utilizados pelo BotService.

CONTRATO LSP:
    - Todos os métodos DEVEM ser assíncronos (async def).
    - Todos os métodos DEVEM levantar apenas subclasses de CanalIntegracaoError.
    - Nunca levante exceções cruas de bibliotecas externas (httpx, requests, etc).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

# Importação para documentação (não usada em runtime, apenas para type hints)
from app.exceptions.canal_exceptions import (
    CanalIntegracaoError,
    CanalAutenticacaoFalhouError,
    CanalEntregaFalhouError,
    CanalLimiteTaxaError,
    CanalMidiaNaoSuportadaError,
)


@runtime_checkable
class BaseCanalAdapter(Protocol):
    """
    Protocol (interface estrutural) que define o comportamento obrigatório
    de qualquer adaptador de canal de comunicação.
    
    Qualquer classe que implementar estes métodos assíncronos será considerada
    um adaptador válido pelo BotService e pela ChannelFactory.
    
    CONTRATO DE EXCEÇÕES (LSP):
        Todos os métodos DEVEM levantar apenas subclasses de CanalIntegracaoError:
        - CanalEntregaFalhouError: Falha de rede, timeout ou erro HTTP >= 400.
        - CanalAutenticacaoFalhouError: Token/APIKey inválido ou expirado (401/403).
        - CanalLimiteTaxaError: Limite de requisições da API externa atingido (429).
        - CanalMidiaNaoSuportadaError: Tipo de mídia não suportado pelo provedor.
    
    Exemplo de uso:
        >>> class WhatsAppAdapter(BaseCanalAdapter):
        ...     async def send_text(self, chat_id: str, text: str, instance: str):
        ...         try:
        ...             response = await httpx.post(...)
        ...         except httpx.TimeoutException as e:
        ...             raise CanalEntregaFalhouError("Timeout", detalhe=str(e)) from e
    """

    async def send_text(
        self, chat_id: str, text: str, instance: str
    ) -> dict[str, Any] | None:
        """
        Envia uma mensagem de texto simples.
        
        Args:
            chat_id: Identificador do destinatário (número de telefone, chat ID, etc).
            text: Conteúdo da mensagem de texto.
            instance: Nome da instância do canal (ex: nome da instância na Evolution API).
        
        Returns:
            dict | None: Resposta da API externa (formato específico do provedor) ou None.
        
        Raises:
            CanalAutenticacaoFalhouError: Se as credenciais forem inválidas.
            CanalEntregaFalhouError: Se a mensagem não puder ser entregue.
            CanalLimiteTaxaError: Se o limite de requisições for atingido.
        """
        ...

    async def send_list(
        self,
        chat_id: str,
        title: str,
        description: str,
        button_text: str,
        sections: list[dict[str, Any]],
        instance: str,
        footer: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Envia uma mensagem interativa do tipo lista/menu.
        
        Args:
            chat_id: Identificador do destinatário.
            title: Título da lista.
            description: Descrição/corpo da mensagem.
            button_text: Texto do botão para abrir a lista.
            sections: Lista de seções com opções (formato específico do provedor).
            instance: Nome da instância do canal.
            footer: Rodapé opcional da mensagem.
        
        Returns:
            dict | None: Resposta da API externa ou None.
        
        Raises:
            CanalAutenticacaoFalhouError: Se as credenciais forem inválidas.
            CanalEntregaFalhouError: Se a mensagem não puder ser entregue.
            CanalMidiaNaoSuportadaError: Se o provedor não suportar listas.
        """
        ...

    async def send_media(
        self,
        chat_id: str,
        media_type: str,
        media_url: str,
        caption: str,
        instance: str,
    ) -> dict[str, Any] | None:
        """
        Envia mídia (imagem, áudio, documento, vídeo).
        
        Args:
            chat_id: Identificador do destinatário.
            media_type: Tipo de mídia ("imagem", "documento", "audio", "video").
            media_url: URL pública da mídia ou caminho local.
            caption: Legenda/descrição da mídia.
            instance: Nome da instância do canal.
        
        Returns:
            dict | None: Resposta da API externa ou None.
        
        Raises:
            CanalAutenticacaoFalhouError: Se as credenciais forem inválidas.
            CanalEntregaFalhouError: Se a mídia não puder ser enviada.
            CanalMidiaNaoSuportadaError: Se o tipo de mídia não for suportado.
        """
        ...


# ══════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════

def validar_adapter(adapter: Any) -> bool:
    """
    Verifica se um objeto implementa o protocolo BaseCanalAdapter.
    
    Args:
        adapter: Objeto a ser validado.
    
    Returns:
        bool: True se o objeto implementa todos os métodos do protocolo.
    
    Exemplo:
        >>> from app.canais.whatsapp_integration import WhatsAppEvolutionAdapter
        >>> adapter = WhatsAppEvolutionAdapter()
        >>> validar_adapter(adapter)
        True
    """
    return isinstance(adapter, BaseCanalAdapter)


__all__ = [
    "BaseCanalAdapter",
    "validar_adapter",
]