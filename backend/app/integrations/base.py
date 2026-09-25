# app/integrations/base.py
"""
Módulo: base.py

Explicação:
Este módulo estabelece a fundação arquitetural do pacote de integrações. 
Ele define as Classes Base Abstratas (ABCs) que atuam como contratos (interfaces). 
Ao obrigar todas as integrações a herdarem destas classes, garantimos o polimorfismo, 
permitindo que o roteador de mensagens da aplicação trate canais distintos de maneira 
uniforme, sem a necessidade de blocos condicionais complexos.

Funcionalidades:
- BaseChannelIntegration: Define o contrato padrão para canais de mensageria (envio de texto, mídia e parsing de webhooks).
- BaseUtilityIntegration: Define o contrato padrão para utilitários de processamento de dados (como OCR e TTS).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseChannelIntegration(ABC):
    """
    Classe Base Abstrata para Canais de Mensageria.
    
    Explicação:
    Estabelece a interface obrigatória para qualquer plataforma de comunicação 
    que envie e receba mensagens (WhatsApp, Telegram, Discord, etc.).
    
    Funcionalidades:
    - send_text_message: Envia mensagens de texto puro.
    - send_media_message: Envia arquivos de mídia (imagem, áudio, vídeo, documento).
    - parse_incoming_webhook: Padroniza a extração de dados de payloads brutos de webhooks.
    """

    @abstractmethod
    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Envia uma mensagem de texto para o destinatário especificado."""
        pass

    @abstractmethod
    async def send_media_message(self, chat_id: str, media_url: str, media_type: str) -> Dict[str, Any]:
        """Envia um arquivo de mídia para o destinatário especificado."""
        pass

    @abstractmethod
    def parse_incoming_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai e padroniza dados (remetente, texto, tipo) do webhook da plataforma."""
        pass


class BaseUtilityIntegration(ABC):
    """
    Classe Base Abstrata para Integrações de Utilitários.
    
    Explicação:
    Estabelece a interface para serviços de processamento e transformação de dados, 
    como Reconhecimento Óptico de Caracteres (OCR) e Síntese de Voz (TTS).
    
    Funcionalidades:
    - process: Executa a tarefa de transformação de dados baseada no motor configurado.
    """

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Processa o dado de entrada e retorna o resultado transformado."""
        pass