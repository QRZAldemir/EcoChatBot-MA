# backend/app/services/pabx_service.py
import httpx
import logging

logger = logging.getLogger(__name__)

class PabxService:
    def __init__(self, db: Session):
        self.db = db

    async def iniciar_chamada_cross_channel(self, canal_id: int, numero_destino: str):
        # 1. Busca o canal no banco
        canal = self.db.query(Canal).filter(Canal.id == canal_id, Canal.tipo == "voip_telefonia").first()
        if not canal:
            raise ValueError("Canal VoIP não encontrado")

        # 2. Desserializa o JSON que está salvo no banco
        config = canal.configuracao_json  # Usa a @property que criamos no modelo Canal
        
        # 3. Extrai as variáveis do seu JSON
        api_url = config.get("api_base_url")
        api_user = config.get("api_user")
        api_secret = config.get("api_secret")
        trunk = config.get("trunk_outbound")
        context = config.get("context_ura")

        # 4. Monta a requisição específica para o provedor (ex: Asterisk ARI)
        if config.get("pabx_type") == "asterisk_ari":
            payload = {
                "endpoint": f"SIP/{trunk}/{numero_destino}",
                "context": context,
                "extension": "s", # Ou a extensão da sua URA
                "priority": 1
            }
            headers = {"Authorization": f"Basic {base64.b64encode(f'{api_user}:{api_secret}'.encode()).decode()}"}
            
            # 5. Dispara a ordem para o PABX do cliente
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{api_url}/channels", json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Chamada iniciada no PABX para {numero_destino}")