from __future__ import annotations

SYSTEM_BASE = (
    "You are YuviGPT, a private assistant running on the user's hardware. "
    "When context excerpts are provided, ground answers in them and cite which "
    "excerpt you used by number (e.g. [1]). If context is missing or insufficient, "
    "say so clearly before using general knowledge."
)


def build_llm_messages(
    messages: list[dict[str, str]],
    context_chunks: list[dict],
    persona_text: str | None = None,
) -> list[dict[str, str]]:
    non_system = [m for m in messages if m.get("role") != "system"]
    context_block = "\n\n".join(
        f"[{i + 1}] ({c['metadata'].get('source', 'doc')}): {c['text']}"
        for i, c in enumerate(context_chunks)
    )
    system_content = SYSTEM_BASE
    if persona_text and persona_text.strip():
        system_content += f"\n\n---\nPersona (follow this style):\n{persona_text.strip()}\n---"
    if context_block.strip():
        system_content += f"\n\n---\nContext:\n{context_block}\n---"
    return [{"role": "system", "content": system_content}, *non_system]


def last_user_query(messages: list[dict[str, str]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content") or ""
    return ""
