# backend/app/services/bot_service.py (refatorado)
class BotService:
    def __init__(self, tenant_id: int):
        self.tenant_config = self._get_tenant_config(tenant_id)
        self.departments = self._get_departments(tenant_id)
    
    def _get_tenant_config(self, tenant_id: int) -> Dict[str, Any]:
        """Busca configuração específica do tenant"""
        # Implementação usando tenant_service
    
    def _get_departments(self, tenant_id: int) -> Dict[str, Any]:
        """Busca departamentos customizados do tenant"""
        # Implementação usando tenant_service
