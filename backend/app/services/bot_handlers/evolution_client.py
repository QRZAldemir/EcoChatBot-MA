"""
================================================================================
CLIENTE DA EVOLUTION API (ENCAPSULADO EM CLASSE OOP)
================================================================================
Arquivo: bot_handlers/evolution_client.py
Propósito: Encapsular toda comunicação com Evolution API em uma classe

ANTES (Anti-pattern):
  evolution_service.py tinha ~50 funções soltas (procedural puro)
  - Sem encapsulamento de estado (URL, chave API)
  - Difícil de testar
  - Sem polimorfismo

DEPOIS (OOP Puro):
  EvolutionApiClient como classe com estado encapsulado
  - ENCAPSULAMENTO: URL, API key, headers privados
  - HERANÇA: Pode ser estendida (ex: EvoAICloud herda de EvolutionApiClient)
  - POLIMORFISMO: Métodos podem ser sobrescrito
  - ABSTRAÇÃO: Esconde detalhes de HTTP
================================================================================
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class EvolutionApiClient:
    """
    CLASSE: Encapsula toda comunicação com Evolution API
    Responsabilidade única (SRP): Gerenciar requisições HTTP para Evolution

    Equivalente em Delphi:
        type
          TEvolutionApiClient = class(TObject)
          private
            FBaseUrl: string;
            FApiKey: string;
            FAuthHeader: string;
          public
            procedure EnviarTexto(...);
            procedure EnviarLista(...);
          end;
    """

    # ──────────────────────────────────────────────────────────────────────────
    # ATRIBUTOS PRIVADOS (Encapsulamento)
    # ──────────────────────────────────────────────────────────────────────────

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_header: str = "apikey",
    ):
        """
        ENCAPSULAMENTO: Inicializa atributos privados

        Args:
            base_url: URL base da Evolution API (ex: http://localhost:8080)
            api_key: Chave de autenticação
            auth_header: Nome do header ("apikey" ou "api_access_token")
        """
        # Atributos privados (convenção Python: prefixo _)
        self._base_url = (base_url or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")).rstrip("/")
        self._api_key = api_key or os.getenv("EVOLUTION_API_KEY", "")
        self._auth_header = auth_header

        # Cliente HTTP assíncrono (mantém conexão aberta)
        self._client = httpx.AsyncClient(timeout=30.0)

        logger.info(
            "EvolutionApiClient inicializado | url=%s | auth_header=%s",
            self._base_url,
            self._auth_header,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTODOS PÚBLICOS (Interface da classe)
    # ──────────────────────────────────────────────────────────────────────────

    async def enviar_texto(self, instance: str, number: str, text: str) -> dict:
        """
        Envia mensagem de texto via WhatsApp

        Args:
            instance: Nome da instância WhatsApp na Evolution
            number: Número do destinatário (ex: "67999999999")
            text: Texto a enviar

        Returns:
            Resposta da API (dict)

        Raises:
            httpx.HTTPStatusError: Se Evolution retornar erro HTTP
            httpx.TimeoutException: Se requisição expirar
        """
        url = f"{self._base_url}/message/sendText/{instance}"
        return await self._fazer_requisicao(
            "POST",
            url,
            json={"number": number, "text": text},
            funcao="enviar_texto",
        )

    async def enviar_lista(
        self,
        instance: str,
        number: str,
        title: str,
        description: str,
        button_text: str,
        rows: list[dict],
        footer: str = "",
    ) -> dict:
        """
        Envia menu interativo (lista com opções)

        Args:
            instance: Nome da instância
            number: Número do destinatário
            title: Título do menu
            description: Descrição
            button_text: Texto do botão
            rows: Lista de opções [{"title": "...", "description": "...", "rowId": "..."}]
            footer: Rodapé (opcional)

        Returns:
            Resposta da API
        """
        url = f"{self._base_url}/message/sendList/{instance}"
        payload = {
            "number": number,
            "title": title,
            "description": description,
            "buttonText": button_text,
            "sections": [{"title": title, "rows": rows}],
        }
        if footer:
            payload["footer"] = footer

        return await self._fazer_requisicao(
            "POST",
            url,
            json=payload,
            funcao="enviar_lista",
        )

    async def enviar_midia(
        self,
        instance: str,
        number: str,
        media_url: str,
        mediatype: str = "audio",
    ) -> dict:
        """
        Envia mídia (áudio, imagem, documento)

        Args:
            instance: Nome da instância
            number: Número destinatário
            media_url: URL pública da mídia
            mediatype: Tipo ("audio", "image", "document", "video")

        Returns:
            Resposta da API
        """
        url = f"{self._base_url}/message/sendMedia/{instance}"
        return await self._fazer_requisicao(
            "POST",
            url,
            json={"number": number, "mediaUrl": media_url, "mediaType": mediatype},
            funcao="enviar_midia",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTODOS PRIVADOS (Implementação interna)
    # ──────────────────────────────────────────────────────────────────────────

    async def _fazer_requisicao(
        self,
        metodo: str,
        url: str,
        json: dict,
        funcao: str,
    ) -> dict:
        """
        ABSTRAÇÃO: Centraliza lógica de requisição HTTP

        Benefícios:
          - Trata erros uma única vez
          - Log centralizado
          - Facilita testes (mocka este método)
          - Reutiliza logic de retry, timeout, etc

        Args:
            metodo: "GET", "POST", "PUT", "DELETE"
            url: URL completa
            json: Payload JSON
            funcao: Nome da função (para logs)

        Returns:
            Resposta JSON da API

        Raises:
            httpx.HTTPStatusError: Se status HTTP >= 400
        """
        try:
            resposta = await self._client.request(
                metodo,
                url,
                headers=self._montar_headers(),
                json=json,
            )
            resposta.raise_for_status()  # Lança exceção se erro HTTP
            return resposta.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "evolution_api | %s | HTTP %s | %s",
                funcao,
                e.response.status_code,
                e.response.text[:200],
            )
            raise

        except httpx.TimeoutException:
            logger.error("evolution_api | %s | timeout", funcao)
            raise

        except Exception as e:
            logger.exception("evolution_api | %s | erro inesperado", funcao)
            raise

    def _montar_headers(self) -> dict:
        """
        ABSTRAÇÃO: Monta headers da requisição

        Permite trocar auth_header sem afetar código chamador
        (útil para EvoAI Cloud que usa "api_access_token" em vez de "apikey")
        """
        return {
            self._auth_header: self._api_key,
            "Content-Type": "application/json",
        }

    async def __aenter__(self):
        """Context manager: async with client as c:"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fecha cliente HTTP ao sair do contexto"""
        await self._client.aclose()
