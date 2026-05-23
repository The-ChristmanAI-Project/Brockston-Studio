"""Ollama Client for Brockston-Studio"""
import requests
import json
from typing import Optional, Dict, Any

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
    
    def chat(self, model: str, messages: list, temperature: float = 0.7) -> str:
        """Send chat request to Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            print(f"Ollama error: {e}")
            return ""
    
    def generate_code(self, prompt: str) -> str:
        """Generate code using qwen2.5-coder"""
        return self.chat(
            model="qwen2.5-coder:32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
    
    def converse(self, message: str, context: list = None) -> str:
        """Have a conversation using llama3.2"""
        messages = context or []
        messages.append({"role": "user", "content": message})
        return self.chat(
            model="llama3.2:3b",
            messages=messages,
            temperature=0.7
        )

# Singleton instance
ollama_client = OllamaClient()
