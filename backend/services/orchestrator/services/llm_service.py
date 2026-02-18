"""
Service LLM - Interface avec les modèles de langage
"""

from typing import List, Optional
from loguru import logger
import os
import httpx
import json


class LLMService:
    """Gère les interactions avec le LLM"""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, anthropic
        self.model = os.getenv("LLM_MODEL", "llama3.1:8b")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        
        if self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
        elif self.provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def generate_answer(
        self,
        query: str,
        contexts: List[str],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Génère une réponse basée sur la requête et les contextes
        """
        # Build the prompt
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        context_text = "\n\n---\n\n".join([ctx for ctx in contexts])
        
        user_prompt = f"""Informations disponibles :
{context_text}

---

Question : {query}

Instructions :
- Répondez de manière précise et détaillée en vous basant UNIQUEMENT sur les informations ci-dessus
- Fournissez tous les détails techniques pertinents disponibles dans le contexte
- Organisez votre réponse de manière structurée (listes à puces, étapes numérotées si approprié)
- Ne mentionnez PAS les numéros de documents ou sources dans votre réponse
- Si le contexte ne contient pas suffisamment d'informations, indiquez-le clairement
- Répondez directement à la question sans préambule inutile"""

        try:
            if self.provider == "ollama":
                return await self._generate_with_ollama(system_prompt, user_prompt)
            elif self.provider == "openai":
                return await self._generate_with_openai(system_prompt, user_prompt)
            elif self.provider == "anthropic":
                return await self._generate_with_anthropic(system_prompt, user_prompt)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    async def _generate_with_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse avec Ollama"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API error: {response.text}")
                
                result = response.json()
                return result["response"].strip()
                
        except Exception as e:
            logger.error(f"Error with Ollama: {e}")
            raise
    
    async def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse avec OpenAI"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.text}")
                
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            logger.error(f"Error with OpenAI: {e}")
            raise
    
    async def _generate_with_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse avec Anthropic Claude"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Anthropic API error: {response.text}")
                
                result = response.json()
                return result["content"][0]["text"].strip()
                
        except Exception as e:
            logger.error(f"Error with Anthropic: {e}")
            raise
    
    def _get_default_system_prompt(self) -> str:
        """Retourne le prompt système par défaut"""
        return """Vous êtes un assistant technique expert spécialisé dans la téléphonie d'entreprise, les solutions Cisco et la plateforme WTE (Webex Teams Edition) d'Orange.

Règles strictes :
1. Répondez UNIQUEMENT en vous basant sur les informations fournies dans le contexte
2. Fournissez des réponses détaillées, précises et complètes avec tous les détails techniques disponibles
3. Ne mentionnez JAMAIS les numéros de documents, les sources ou que vous vous basez sur des documents
4. Répondez comme si vous connaissiez ces informations de manière naturelle
5. Utilisez un format structuré (listes, étapes, sections) pour une meilleure lisibilité
6. Si l'information n'est pas disponible dans le contexte, indiquez simplement que vous n'avez pas cette information
7. Soyez technique mais compréhensible
8. Répondez en français de manière professionnelle et directe"""
