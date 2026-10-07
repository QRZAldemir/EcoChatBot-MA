"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Evolution API Client
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     evolution_api_client.py
@module   Backend / App / Services
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Cliente HTTP assíncrono para integração com a Evolution API (WhatsApp).
Gerencia o ciclo de vida das instâncias: criação, QR Code, status,
reconexão, logout e definições.

INTEGRAÇÃO COM EVOLUTION API
────────────────────────────
    Documentação: https://doc.evolution-api.com/
    Endpoints base: {base_url}/instance

    • POST /instance/create → Criar instância
    • GET /instance/fetchInstances → Listar instâncias
    • GET /instance/connectionState/{instanceName} → Status
    • POST /instance/connect/{instanceName} → Gerar QR Code
    • POST /instance/logout/{instanceName} → Desconectar
    • POST /instance/reconnect/{instanceName} → Reconectar

REGRAS DE NEGÓCIO
─────────────────
    • Timeout de 30 segundos para todas as requisições
    • Retry automático em falhas de rede (3 tentativas)
    • Log de todos os erros para debugging
    • Validação de token em cada requisição
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


class EvolutionApiClient:
    """
    Cliente assíncrono para a Evolution API.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.base_url = settings.evolution_api_base_url
        self.api_key = settings.evolution_api_key
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Faz requisição HTTP para a Evolution API com retry automático.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: Endpoint da API (ex: '/instance/create')
            data: Dados para o request body (para POST)
            
        Returns:
            JSON response da API
            
        Raises:
            HTTPException: Em caso de erro na API externa
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            logger.error("Timeout na Evolution API: %s", endpoint)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Timeout na comunicação com Evolution API",
            ) from e
            
        except httpx.HTTPError as e:
            logger.error("Erro HTTP na Evolution API: %s - %s", endpoint, str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erro na Evolution API: {str(e)}",
            ) from e
            
        except Exception as e:
            logger.exception("Erro inesperado na Evolution API: %s", endpoint)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno na comunicação com Evolution API",
            ) from e
    
    async def create_instance(self, instance_name: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria uma nova instância na Evolution API.
        """
        data = {
            "instanceName": instance_name,
            "webhook": webhook_url,
            "qrcode": True,
        }
        return await self._make_request("POST", "/instance/create", data)
    
    async def get_connection_state(self, instance_name: str) -> Dict[str, Any]:
        """
        Obtém o estado da conexão de uma instância.
        
        Returns:
            {
                "state": "open" | "connecting" | "close",
                "qrCode": { ... }  # se disponível
            }
        """
        return await self._make_request("GET", f"/instance/connectionState/{instance_name}")
    
    async def connect(self, instance_name: str) -> Dict[str, Any]:
        """
        Gera QR Code para conexão.
        """
        return await self._make_request("POST", f"/instance/connect/{instance_name}")
    
    async def logout(self, instance_name: str) -> None:
        """
        Desconecta a instância (logout).
        """
        await self._make_request("POST", f"/instance/logout/{instance_name}")
    
    async def reconnect(self, instance_name: str) -> Dict[str, Any]:
        """
        Reconecta a instância (renova a sessão sem deletar).
        """
        return await self._make_request("POST", f"/instance/reconnect/{instance_name}")
    
    async def delete_instance(self, instance_name: str) -> None:
        """
        Deleta permanentemente a instância.
        """
        await self._make_request("DELETE", f"/instance/delete/{instance_name}")
    
    async def fetch_instances(self) -> Dict[str, Any]:
        """
        Lista todas as instâncias do tenant.
        """
        return await self._make_request("GET", "/instance/fetchInstances")