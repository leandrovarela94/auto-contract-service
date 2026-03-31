"""
Ollama Client — Conexão com Ollama Cloud via API REST.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class OllamaClient:
    """Client para Ollama Cloud usando API REST direta."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://ollama.com",
        model: str = "llama3.2:latest",
    ):
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "")
        self.base_url = base_url
        self.model = model

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
        """Gera texto usando Ollama Cloud."""
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY não configurada")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )

            if response.status_code == 401:
                raise Exception("API Key inválida ou expirada")
            if response.status_code == 404:
                raise Exception(f"Modelo '{self.model}' não encontrado")

            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    def generate_json(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Gera e parseia JSON."""
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


ollama_client = OllamaClient()
