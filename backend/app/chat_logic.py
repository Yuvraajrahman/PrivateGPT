from __future__ import annotations

import re

_REDACT = "[repository link omitted]"

# HTTPS remotes and common Git hosting (markdown-safe: stops before closing paren/quote).
_GIT_HTTP = re.compile(
    r"(?i)\bhttps?://(?:www\.)?(?:github|gitlab)\.com/[^\s\])>'\"]+|"
    r"\bhttps?://(?:www\.)?bitbucket\.org/[^\s\])>'\"]+"
)
_GIT_HTTP_BARE = re.compile(
    r"(?i)\b(?:www\.)?(?:github|gitlab)\.com/[\w./-]+(?:\.git)?\b|"
    r"\b(?:www\.)?bitbucket\.org/[\w./-]+(?:\.git)?\b"
)
_GIST_HTTP = re.compile(r"(?i)\bhttps?://gist\.github\.com/[^\s\])>'\"]+")
_RAW_GITHUB = re.compile(r"(?i)\bhttps?://raw\.githubusercontent\.com/[^\s\])>'\"]+")
_GIT_SSH = re.compile(r"(?i)\bgit@[\w.-]+:[\w./-]+(?:\.git)?\b")
_SSH_URL = re.compile(r"(?i)\bssh://[^\s\])>'\"]+")


def redact_git_remote_urls(text: str) -> str:
    """Strip common Git hosting URLs before they reach the model."""
    if not text:
        return text
    t = _GIT_HTTP.sub(_REDACT, text)
    t = _GIT_HTTP_BARE.sub(_REDACT, t)
    t = _GIST_HTTP.sub(_REDACT, t)
    t = _RAW_GITHUB.sub(_REDACT, t)
    t = _GIT_SSH.sub(_REDACT, t)
    t = _SSH_URL.sub(_REDACT, t)
    return t


def _context_line(i: int, c: dict) -> str:
    meta = c.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    source = redact_git_remote_urls(str(meta.get("source", "doc") or "doc"))
    body = redact_git_remote_urls(str(c.get("text") or ""))
    return f"[{i + 1}] ({source}): {body}"


SYSTEM_BASE = (
    "You are YuviGPT, a private assistant running on the user's hardware. "
    "Your job is to answer questions about Yuvraj's portfolio, projects, and skills, "
    "while mimicking Yuvraj's communication style. "
    "When context excerpts are provided, ground answers in them and cite which "
    "excerpt you used by number (e.g. [1]). If context is missing or insufficient, "
    "say so clearly before using general knowledge. "
    "Do not share Git hosting URLs (GitHub, GitLab, Bitbucket), git@… clone strings, "
    "or other private repository URLs—even if they appeared in context before redaction. "
    "Refer to repositories by project name only."
)


def build_llm_messages(
    messages: list[dict[str, str]],
    context_chunks: list[dict],
    persona_text: str | None = None,
) -> list[dict[str, str]]:
    non_system = [m for m in messages if m.get("role") != "system"]
    context_block = "\n\n".join(
        _context_line(i, c)
        for i, c in enumerate(context_chunks)
    )
    system_content = SYSTEM_BASE
    if persona_text and persona_text.strip():
        system_content += (
            f"\n\n---\nPersona (follow this style):\n{redact_git_remote_urls(persona_text.strip())}\n---"
        )
    if context_block.strip():
        system_content += f"\n\n---\nContext:\n{context_block}\n---"
    return [{"role": "system", "content": system_content}, *non_system]


def last_user_query(messages: list[dict[str, str]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content") or ""
    return ""
