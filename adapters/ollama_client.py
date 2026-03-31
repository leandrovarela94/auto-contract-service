"""
Ollama Client — Conexão com Ollama rodando localmente via API REST.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


class OllamaClient:
    """Client para Ollama rodando localmente."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.3",
    ):
        self.base_url = base_url
        self.model = model

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> str:
        """Gera texto usando Ollama local."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            if response.status_code == 404:
                raise Exception(
                    f"Modelo '{self.model}' não encontrado. Execute: ollama pull {self.model}"
                )

            if response.status_code != 200:
                raise Exception(f"Erro Ollama: {response.status_code}")

            data = response.json()
            return data["message"]["content"].strip()

    def generate_json(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Gera e parseia JSON."""
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
