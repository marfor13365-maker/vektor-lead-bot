import requests
from typing import Optional, Dict, Any

class Grok:
    """Клиент для работы с Grok API (xAI)"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self):
        return self
    
    def completions(self):
        return self
    
    def create(self, model: str, messages: list, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        """Отправляет запрос к Grok API"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
