"""
Ollama Adapter — Conexão com Ollama Cloud API.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx


class OllamaAdapter:
    """Adapter para Ollama Cloud (API OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.ollama.com/v1",
        model: str = "llama3.2",
    ):
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "ollama")
        self.base_url = base_url
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> str:
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY não configurada")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    )

                    if response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        raise Exception("Rate limit excedido. Aguarde alguns segundos.")

                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()

            except httpx.HTTPStatusError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"Erro HTTP: {e.response.status_code}")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise

        return ""

    def generate_json(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        import json

        text = self.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            temperature=temperature,
        )
        clean = text.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()
        return json.loads(clean)


ollama_adapter = OllamaAdapter()
