from typing import Any, Dict
# backend/app/services/bot_handlers/dynamic_flow.py
class DynamicFlow:
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self.flow_config = self._load_flow_config()
    
    def _load_flow_config(self) -> Dict[str, Any]:
        # Carrega configuração de fluxo do tenant
        pass
