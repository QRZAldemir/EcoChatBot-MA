import httpx
import os
from typing import List, Dict

class DeepSeekService:

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    async def conversar(self, mensagens: List[Dict[str, str]], canal: str) -> Dict:
        if not self.api_key:
            return {"resposta": "Serviço de IA não configurado. Configure DEEPSEEK_API_KEY.", "tokens": 0}

        system_message = {
            "role": "system",
            "content": (
                f"Você é um assistente virtual do Hospital Marcx atendendo pelo canal '{canal}'. "
                "Seja profissional, empático e objetivo nas respostas. "
                "Responda sempre em português do Brasil."
            )
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [system_message] + mensagens,
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
                return {"resposta": f"Erro na API DeepSeek: {response.status_code}", "tokens": 0}
        except Exception as e:
            return {"resposta": f"Erro ao comunicar com IA: {str(e)}", "tokens": 0}

    async def responder_opcao(self, opcao: str, canal: str, contexto: str = "") -> Dict:
        prompt = (
            f"Canal: {canal}\n"
            f"Opção selecionada pelo paciente: {opcao}\n"
            f"Contexto adicional: {contexto}\n\n"
            "Gere uma resposta apropriada e profissional para esta opção no contexto do Hospital Marcx."
        )
        return await self.conversar([{"role": "user", "content": prompt}], canal)
