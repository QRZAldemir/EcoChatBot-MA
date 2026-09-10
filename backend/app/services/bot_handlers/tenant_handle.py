# backend/app/services/bot_handlers/tenant_handler.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class TenantHandler(ABC):
    @abstractmethod
    def get_tenant_config(self, tenant_id: int) -> Dict[str, Any]:
        """Retorna configuração específica do tenant"""
        pass
    
    @abstractmethod
    def get_departments(self, tenant_id: int) -> Dict[str, Any]:
        """Retorna departamentos customizados do tenant"""
        pass
