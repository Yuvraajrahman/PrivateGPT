from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    parts: list[dict[str, Any]] | None = None


class ChatRequestBody(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    # AI SDK may send extra fields (id, trigger, etc.)
    model_config = {"extra": "ignore"}


def normalize_messages(raw: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in raw:
        role = m.get("role")
        if not role:
            continue
        content = m.get("content")
        if content is None and isinstance(m.get("parts"), list):
            texts: list[str] = []
            for p in m["parts"]:
                if isinstance(p, dict) and p.get("type") == "text":
                    t = p.get("text")
                    if isinstance(t, str):
                        texts.append(t)
            content = "".join(texts)
        if content is None:
            continue
        if not isinstance(content, str):
            content = str(content)
        out.append({"role": str(role), "content": content})
    return out
