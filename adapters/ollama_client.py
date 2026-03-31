"""
Ollama Client — Conexão com Ollama Cloud via biblioteca Python.
"""

from __future__ import annotations

import os
from typing import Any

import ollama


class OllamaClient:
    """Client para Ollama Cloud usando a biblioteca oficial."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.ollama.com",
        model: str = "gpt-oss:120b-cloud",
    ):
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy initialization do client."""
        if self._client is None:
            self._client = ollama.Client(host=self.base_url)
        return self._client

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> str:
        """Gera texto usando Ollama."""
        try:
            client = self._get_client()
            response = client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"].strip()
        except Exception as e:
            raise Exception(f"Erro ao gerar: {str(e)}")

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
