# ==============================================================================
# ARQUIVO.....: whatsapp_integration.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Adaptador de Integração WhatsApp (Evolution API)
# VERSÃO......: 2.0.0 (Refatorado para LSP com Exceções de Domínio)
# CRIADO EM...: 2026-10-07
# ATUALIZADO..: 2026-10-09
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: httpx (Async HTTP Client)
# ==============================================================================
# DESCRIÇÃO...:
# Adaptador concreto para integração com WhatsApp via Evolution API v2.
#
# FUNCIONALIDADE:
#   - Implementa a interface BaseChannelAdapter para envio de mensagens.
#   - Traduz erros brutos do httpx/Evolution API para exceções de domínio (LSP).
#   - Garante que o BotService trate falhas de forma unificada, independente do provedor.
#   - Suporta envio de texto, listas interativas e mídias.
#
# RELACIONAMENTOS:
#   - Implementa: app.channels.base.BaseChannelAdapter
#   - Registrado em: app.channels.factory (via @register_channel("whatsapp"))
#   - Utiliza: app.exceptions.canal_exceptions (Exceções de domínio para integração)
#   - Depende de: app.core.config.settings (Credenciais da Evolution API)
# ==============================================================================
"""
Adaptador concreto para WhatsApp (Evolution API).

Responsável por encapsular toda a comunicação HTTP com a Evolution API,
traduzindo erros de rede/HTTP para exceções de domínio canônicas (LSP).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.channels.base import BaseChannelAdapter
from app.channels.factory import register_channel
from app.core.config import settings
from app.exceptions.canal_exceptions import (
    CanalAutenticacaoFalhouError,
    CanalEntregaFalhouError,
    CanalLimiteTaxaError,
    CanalMidiaNaoSuportadaError,
)

logger = logging.getLogger(__name__)


@register_channel("whatsapp")
class WhatsAppEvolutionAdapter(BaseChannelAdapter):
    """
    Adaptador para integração com WhatsApp via Evolution API v2.
    
    CONTRATO LSP:
    Todos os métodos públicos DEVEM levantar apenas subclasses de CanalIntegracaoError.
    Nunca levante httpx.HTTPError, httpx.TimeoutException ou similares diretamente.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Inicializa o adaptador com as credenciais da Evolution API.
        """
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.timeout = settings.EVOLUTION_API_TIMEOUT or 10.0
        
        if not self.base_url or not self.api_key:
            raise ValueError(
                "Credenciais da Evolution API não configuradas nas variáveis de ambiente."
            )

    @property
    def _headers(self) -> dict[str, str]:
        """Cabeçalhos padrão para autenticação na Evolution API."""
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    # ══════════════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS (CONTRATO BaseChannelAdapter)
    # ══════════════════════════════════════════════════════════════════════

    async def send_text(
        self, chat_id: str, text: str, instance: str
    ) -> dict[str, Any] | None:
        """
        Envia mensagem de texto simples via Evolution API.
        
        Raises:
            CanalAutenticacaoFalhouError: Se o token for inválido (401/403).
            CanalLimiteTaxaError: Se o limite de requisições for atingido (429).
            CanalEntregaFalhouError: Se a API retornar erro genérico ou timeout.
        """
        url = f"{self.base_url}/message/sendText/{instance}"
        payload = {
            "number": chat_id,
            "text": text,
        }
        
        return await self._executar_request("POST", url, json=payload)

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
        Envia mensagem interativa do tipo lista/menu via Evolution API.
        
        Raises:
            CanalAutenticacaoFalhouError: Se o token for inválido.
            CanalLimiteTaxaError: Se o limite for atingido.
            CanalEntregaFalhouError: Se a API falhar.
        """
        url = f"{self.base_url}/message/sendList/{instance}"
        payload = {
            "number": chat_id,
            "title": title,
            "description": description,
            "buttonText": button_text,
            "sections": sections,
            "footer": footer or "",
        }
        
        return await self._executar_request("POST", url, json=payload)

    async def send_media(
        self, 
        chat_id: str, 
        media_type: str, 
        media_url: str, 
        caption: str, 
        instance: str
    ) -> dict[str, Any] | None:
        """
        Envia mídia (imagem, áudio, documento) via Evolution API.
        
        Raises:
            CanalMidiaNaoSuportadaError: Se o tipo de mídia não for suportado.
            CanalEntregaFalhouError: Se a API falhar ao processar a mídia.
        """
        # Mapeia o tipo genérico para o endpoint específico da Evolution API
        endpoint_map = {
            "imagem": "sendMediaImage",
            "documento": "sendMediaDocument",
            "audio": "sendMediaAudio",
            "video": "sendMediaVideo",
        }
        
        endpoint = endpoint_map.get(media_type.lower())
        if not endpoint:
            raise CanalMidiaNaoSuportadaError(
                f"Tipo de mídia '{media_type}' não suportado pela Evolution API.",
                detalhe=f"Tipos suportados: {list(endpoint_map.keys())}"
            )
        
        url = f"{self.base_url}/message/{endpoint}/{instance}"
        payload = {
            "number": chat_id,
            "media": media_url,
            "caption": caption,
        }
        
        return await self._executar_request("POST", url, json=payload)

    # ══════════════════════════════════════════════════════════════════════
    # MÉTODO PRIVADO: EXECUÇÃO DE REQUEST COM TRADUÇÃO LSP
    # ══════════════════════════════════════════════════════════════════════

    async def _executar_request(
        self, 
        method: str, 
        url: str, 
        **kwargs: Any
    ) -> dict[str, Any] | None:
        """
        Executa uma requisição HTTP e traduz erros para exceções de domínio (LSP).
        
        Este método centraliza toda a lógica de tratamento de erros, garantindo
        que os métodos públicos (send_text, send_list, send_media) levantem
        apenas exceções canônicas do domínio.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method, 
                    url, 
                    headers=self._headers, 
                    **kwargs
                )
                
                # TRADUÇÃO LSP: HTTP Status -> Exceção de Domínio
                if response.status_code in (401, 403):
                    raise CanalAutenticacaoFalhouError(
                        "Falha de autenticação na Evolution API.",
                        detalhe=response.text
                    )
                
                if response.status_code == 429:
                    raise CanalLimiteTaxaError(
                        "Limite de requisições da Evolution API atingido.",
                        detalhe=response.text
                    )
                
                if response.status_code >= 400:
                    raise CanalEntregaFalhouError(
                        f"Evolution API retornou erro HTTP {response.status_code}.",
                        detalhe=response.text
                    )
                
                # Sucesso: retorna o JSON da resposta
                return response.json()

        except httpx.TimeoutException as e:
            # TRADUÇÃO LSP: Timeout de Rede -> Exceção de Domínio
            logger.error("Timeout ao contatar Evolution API | url=%s", url)
            raise CanalEntregaFalhouError(
                "Timeout ao contatar a Evolution API.",
                detalhe=str(e)
            ) from e
            
        except httpx.RequestError as e:
            # TRADUÇÃO LSP: Erro de Conexão -> Exceção de Domínio
            logger.error("Erro de rede ao contatar Evolution API | url=%s | erro=%s", url, e)
            raise CanalEntregaFalhouError(
                "Erro de rede ao contatar a Evolution API.",
                detalhe=str(e)
            ) from e
            
        except (CanalAutenticacaoFalhouError, CanalLimiteTaxaError, CanalEntregaFalhouError):
            # Re-levanta exceções de domínio sem modificação
            raise
            
        except Exception as e:
            # Fallback para erros inesperados (ex: JSONDecodeError)
            logger.exception("Erro inesperado na Evolution API | url=%s", url)
            raise CanalEntregaFalhouError(
                "Erro inesperado ao processar resposta da Evolution API.",
                detalhe=str(e)
            ) from e


__all__ = ["WhatsAppEvolutionAdapter"]