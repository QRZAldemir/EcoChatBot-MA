# app/adapters/base_message_adapter.py
"""
Módulo: base_message_adapter.py

Explicação:
Define a classe abstrata base BaseMessageAdapter que estabelece o contrato
padrão para adaptação de provedores de mensagens. Seguindo princípios de
interfaces e abstração, esta camada isola o serviço de envio/recepção de
mensagens dos provedores específicos (Evolution API, Meta Cloud API,
Telegram Bot API e PABX/VoIP), permitindo acoplamento polimórfico.

Funcionalidades:
- Interface única para envio de texto, mídia e listas
- Parsing padronizado de webhooks recebidos
- Abstração de provedores para facilitar trocas e testes
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMessageAdapter(ABC):
    """
    Classe Base Abstrata para Adaptadores de Provedores de Mensagem.

    Explicação:
    Estabelece a interface obrigatória para qualquer provedor de mensagens.
    Garante polimorfismo entre diferentes provedores, isolando a camada
    de negócio da implementação específica de cada API.

    Provedores suportados:
    - Evolution API (WhatsApp)
    - Meta Cloud API (WhatsApp Business Cloud)
    - Telegram Bot API
    - PABX/VoIP (MicroSIP, Asterisk, etc.)
    """

    @abstractmethod
    async def send_text(
        self,
        chat_id: str,
        text: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto puro.

        Args:
            chat_id: Identificador do destinatário (número, chat_id, etc.)
            text: Texto da mensagem
            **kwargs: Parâmetros específicos do provedor

        Returns:
            Resposta padronizada do provedor
        """
        pass

    @abstractmethod
    async def send_media(
        self,
        chat_id: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Envia arquivo de mídia (imagem, áudio, vídeo, documento).

        Args:
            chat_id: Identificador do destinatário
            media_url: URL pública do arquivo
            media_type: Tipo de mídia (image, video, audio, document)
            caption: Legenda opcional
            **kwargs: Parâmetros específicos do provedor

        Returns:
            Resposta padronizada do provedor
        """
        pass

    @abstractmethod
    async def send_list(
        self,
        chat_id: str,
        title: str,
        description: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        footer: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Envia lista interativa (menu com opções).

        Args:
            chat_id: Identificador do destinatário
            title: Título da lista
            description: Descrição da lista
            button_text: Texto do botão
            sections: Seções com opções
            footer: Rodapé opcional
            **kwargs: Parâmetros específicos do provedor

        Returns:
            Resposta padronizada do provedor
        """
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai e padroniza dados do webhook do provedor.

        Args:
            payload: Payload bruto recebido do webhook

        Returns:
            Dicionário padronizado com:
            - sender: Identificador do remetente
            - chat_id: Identificador do chat
            - text: Texto da mensagem (se houver)
            - type: Tipo da mensagem (text, media, interactive, etc.)
            - raw: Payload original
        """
        pass
