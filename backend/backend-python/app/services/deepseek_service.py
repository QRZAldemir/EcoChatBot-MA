import httpx
import os
from typing import List, Dict

class DeepSeekService:
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def conversar(self, mensagens: List[Dict[str, str]], canal: str) -> Dict:
        """
        Enviar conversa para DeepSeek e obter resposta
        
        Args:
            mensagens: Lista de mensagens no formato [{"role": "user|assistant", "content": "..."}]
            canal: Nome do canal de atendimento
        
        Returns:
            Dict com resposta da IA
        """
        if not self.api_key:
            return {
                "resposta": "Serviço de IA não configurado. Configure DEEPSEEK_API_KEY.",
                "tokens": 0
            }
        
        # Adicionar contexto do canal
        system_message = {
            "role": "system",
            "content": f"Você é um assistente virtual do Hospital Mackenzie atendendo pelo canal '{canal}'. "
                      f"Seja profissional, empático e objetivo nas respostas. "
                      f"Responda sempre em português do Brasil."
        }
        
        mensagens_com_sistema = [system_message] + mensagens
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": mensagens_com_sistema,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "resposta": data["choices"][0]["message"]["content"],
                        "tokens": data.get("usage", {}).get("total_tokens", 0)
                    }
                else:
                    return {
                        "resposta": f"Erro na API DeepSeek: {response.status_code}",
                        "tokens": 0
                    }
                    
        except Exception as e:
            return {
                "resposta": f"Erro ao comunicar com IA: {str(e)}",
                "tokens": 0
            }
    
    async def responder_opcao(self, opcao: str, canal: str, contexto: str = "") -> Dict:
        """
        Gerar resposta para uma opção específica selecionada pelo usuário
        
        Args:
            opcao: Opção selecionada pelo usuário
            canal: Canal de atendimento
            contexto: Contexto adicional da conversa
        
        Returns:
            Dict com resposta da IA
        """
        prompt = f"""
        Canal: {canal}
        Opção selecionada pelo paciente: {opcao}
        Contexto adicional: {contexto}
        
        Gere uma resposta apropriada e profissional para esta opção no contexto do Hospital Mackenzie.
        """
        
        mensagens = [
            {"role": "user", "content": prompt}
        ]
        
        return await self.conversar(mensagens, canal)
