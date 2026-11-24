"""Small client for the TAMU AI chat API (OpenAI-compatible chat completions)."""
from __future__ import annotations

import os

import requests


class TamusClient:
    def __init__(self, api_key: str, api_base: str = "https://chat-api.tamu.ai", timeout: int = 120):
        self.url = api_base.rstrip("/") + "/api/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.timeout = timeout

    def chat(self, model: str, messages: list[dict], max_tokens: int = 8096,
             temperature: float = 0.0) -> str:
        body = {"model": model, "messages": messages, "max_tokens": max_tokens,
                "temperature": temperature, "stream": False}
        response = requests.post(self.url, headers=self.headers, json=body, timeout=self.timeout)
        response.raise_for_status()
        choices = response.json().get("choices") or []
        content = choices[0].get("message", {}).get("content") if choices else None
        if not content:
            raise ValueError("TAMUS response had no content")
        return content


def get_tamus_client(api_key: str | None = None, api_base: str | None = None) -> TamusClient:
    key = (api_key or os.getenv("TAMUS_API_KEY") or "").strip()
    if not key:
        raise ValueError("TAMUS_API_KEY not set")
    return TamusClient(key, api_base or os.getenv("TAMUS_API_BASE", "https://chat-api.tamu.ai"))
