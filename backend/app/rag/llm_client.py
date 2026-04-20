from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import Settings


async def stream_openai_compatible(
    settings: Settings,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    client = AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )
    stream = await client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        stream=True,
        temperature=0.2,
    )
    async for event in stream:
        choice = event.choices[0] if event.choices else None
        if not choice:
            continue
        delta = choice.delta
        if delta and delta.content:
            yield delta.content


async def stream_ollama(
    settings: Settings,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=600.0) as client:
        async with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message") or {}
                piece = msg.get("content")
                if piece:
                    yield piece
                if data.get("done"):
                    break


async def stream_llm(
    settings: Settings,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    if settings.llm_provider == "ollama":
        async for t in stream_ollama(settings, messages):
            yield t
    else:
        async for t in stream_openai_compatible(settings, messages):
            yield t
