"""
AI Client — Conexão com Groq API (gratuito) e fallback Gemini.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


class AIClient:
    """Client para IA usando Groq (principal) e Gemini (fallback)."""

    def __init__(
        self,
        groq_api_key: str | None = None,
        gemini_api_key: str | None = None,
        groq_model: str = "llama-3.3-70b-versatile",
    ):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.groq_model = groq_model

    def _groq_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> str:
        """Gera texto usando Groq (principal) ou Gemini (fallback)."""

        if self.groq_api_key:
            try:
                return self._groq_generate(
                    system_instruction, user_prompt, temperature, max_tokens
                )
            except Exception as groq_err:
                if self.gemini_api_key:
                    return self._gemini_generate(system_instruction, user_prompt)
                raise groq_err

        elif self.gemini_api_key:
            return self._gemini_generate(system_instruction, user_prompt)

        raise ValueError("Configure GROQ_API_KEY ou GEMINI_API_KEY")

    def _groq_generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Gera usando Groq API."""
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=self._groq_headers(),
                json=payload,
            )

            if response.status_code == 401:
                raise Exception("GROQ_API_KEY inválida")

            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    def _gemini_generate(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> str:
        """Gera usando Gemini API."""
        import json

        payload = {
            "contents": [
                {"parts": [{"text": f"{system_instruction}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 4000,
            },
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )

            if response.status_code == 401:
                raise Exception("GEMINI_API_KEY inválida")

            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

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


ai_client = AIClient()
