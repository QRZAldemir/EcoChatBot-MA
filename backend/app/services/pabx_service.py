"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: services/pabx_service.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Orquestrar o gateway de Telefonia IPVoIP/PABX. Processa eventos de chamada,
navegação por DTMF (URA), transcrição de voz (STT) e geração de respostas
sintetizadas (TTS) utilizando o DeepSeekService para inteligência artificial.

ARQUITETURA E INTEGRAÇÃO:
Camada de Serviço de Domínio. Consome `DeepSeekService`, `STTService` e 
`TTSService`. Expõe seus métodos para o `pabx_router.py`.
================================================================================
"""
from app.services.deepseek_service import DeepSeekService

class PabxService:
    def __init__(self, stt_service, tts_service, ai_service: DeepSeekService):
        self.stt = stt_service
        self.tts = tts_service
        self.ai = ai_service

    async def processar_evento_chamada(self, evento: dict):
        tipo_evento = evento.get("tipo")
        
        if tipo_evento == "dtmf":
            return await self._navegar_menu_ura(evento.get("tecla"))
            
        elif tipo_evento == "audio":
            # 1. Transcrever áudio do cliente (STT)
            transcricao = await self.stt.transcrever(evento["audio_url"])
            
            # 2. Gerar resposta inteligente via IA (DeepSeek)
            resposta_ia = await self.ai.gerar_resposta(transcricao)
            
            # 3. Sintetizar resposta em áudio (TTS)
            audio_resposta_url = await self.tts.sintetizar(resposta_ia)
            
            return {"acao": "reproduzir_audio", "audio_url": audio_resposta_url}
            
        return {"acao": "nenhuma"}

    async def _navegar_menu_ura(self, tecla: str):
        # Lógica de roteamento por tecla (ex: 1 para Vendas, 2 para Suporte)
        return {"acao": "transferir", "fila": f"fila_{tecla}"}