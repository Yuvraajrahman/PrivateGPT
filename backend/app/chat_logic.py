from __future__ import annotations

import re
from collections.abc import AsyncIterator, Sequence

_REDACT = "[repository link omitted]"
_REDACT_MD = "[link omitted]"
_REDACT_HANDLE = "[identity omitted]"

# Markdown: [label](https://github.com/...)
_MD_GIT_LINK = re.compile(
    r"(?i)\[[^\]]{0,500}\]\(\s*https?://(?:www\.)?(?:github|gitlab)\.com[^)]{0,800}\)"
)
_MD_BB_LINK = re.compile(
    r"(?i)\[[^\]]{0,500}\]\(\s*https?://(?:www\.)?bitbucket\.org[^)]{0,800}\)"
)

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
    """Strip common Git hosting URLs before they reach the model (or from streamed output)."""
    if not text:
        return text
    t = _MD_GIT_LINK.sub(_REDACT_MD, text)
    t = _MD_BB_LINK.sub(_REDACT_MD, t)
    t = _GIT_HTTP.sub(_REDACT, t)
    t = _GIT_HTTP_BARE.sub(_REDACT, t)
    t = _GIST_HTTP.sub(_REDACT, t)
    t = _RAW_GITHUB.sub(_REDACT, t)
    t = _GIT_SSH.sub(_REDACT, t)
    t = _SSH_URL.sub(_REDACT, t)
    return t


def redact_identity_handles(text: str, handles: Sequence[str]) -> str:
    """Remove configured Git host usernames / @handles (case-insensitive, word boundaries)."""
    if not text or not handles:
        return text
    t = text
    for h in handles:
        h = h.strip()
        if len(h) < 2:
            continue
        pat = re.compile(rf"(?i)\b@?{re.escape(h)}\b")
        t = pat.sub(_REDACT_HANDLE, t)
    return t


def apply_private_redaction(text: str, handles: Sequence[str]) -> str:
    """URLs + configured identity handles (order: URLs first, then handles)."""
    return redact_identity_handles(redact_git_remote_urls(text), handles)


def strip_trailing_incomplete_git_url(text: str) -> str:
    """Remove an unfinished https://github.com/... tail (streaming flush)."""
    return re.sub(
        r"(?i)https?://(?:www\.)?(?:github|gitlab)\.com(?:[/\w.-]*)?$",
        "",
        re.sub(r"(?i)https?://(?:www\.)?bitbucket\.org(?:[/\w.-]*)?$", "", text),
    ).rstrip()


def _stream_redact_buffer(buf: str, handles: Sequence[str]) -> str:
    u = redact_git_remote_urls(buf)
    u = strip_trailing_incomplete_git_url(u)
    return redact_identity_handles(u, handles)


async def scrub_git_urls_from_stream(
    stream: AsyncIterator[str],
    handles: Sequence[str],
    hold: int = 128,
) -> AsyncIterator[str]:
    """Redact URLs + identity markers across token chunks; hold back a tail for partial URLs."""
    buf = ""
    emitted = 0
    async for piece in stream:
        buf += piece
        safe = _stream_redact_buffer(buf, handles)
        limit = max(0, len(safe) - hold)
        if limit > emitted:
            yield safe[emitted:limit]
            emitted = limit
    tail = _stream_redact_buffer(buf, handles)
    if emitted < len(tail):
        yield tail[emitted:]


def _context_line(i: int, c: dict, handles: Sequence[str]) -> str:
    meta = c.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    source = apply_private_redaction(str(meta.get("source", "doc") or "doc"), handles)
    body = apply_private_redaction(str(c.get("text") or ""), handles)
    return f"[{i + 1}] ({source}): {body}"


SYSTEM_BASE = (
    "You are YuviGPT, a private assistant running on the user's hardware. "
    "Your job is to answer questions about Yuvraj's portfolio, projects, and skills, "
    "while mimicking Yuvraj's communication style. "
    "When context excerpts are provided, ground answers in them and cite which "
    "excerpt you used by number (e.g. [1]). If context is missing or insufficient, "
    "say so clearly before using general knowledge. "
    "Do not share Git hosting URLs (GitHub, GitLab, Bitbucket), git@… clone strings, "
    "or other repository web links—even if they appeared in context before redaction. "
    "Never output markdown links to github.com / gitlab.com / bitbucket.org, and never "
    "reconstruct those URLs from a username or handle. "
    "Do not name or quote this owner's Git hosting usernames, @handles, or profile identities "
    "(they may appear as [identity omitted] in context). "
    "If the user asks for a git address, GitHub username, profile URL, or clone link, refuse briefly "
    "and offer project names or skills instead. "
    "Refer to repositories by project name only."
)


def build_llm_messages(
    messages: list[dict[str, str]],
    context_chunks: list[dict],
    persona_text: str | None = None,
    redact_handles: Sequence[str] | None = None,
) -> list[dict[str, str]]:
    handles = list(redact_handles or [])
    non_system = [m for m in messages if m.get("role") != "system"]
    context_block = "\n\n".join(
        _context_line(i, c, handles)
        for i, c in enumerate(context_chunks)
    )
    system_content = SYSTEM_BASE
    if persona_text and persona_text.strip():
        system_content += (
            f"\n\n---\nPersona (follow this style):\n"
            f"{apply_private_redaction(persona_text.strip(), handles)}\n---"
        )
    if context_block.strip():
        system_content += f"\n\n---\nContext:\n{context_block}\n---"
    return [{"role": "system", "content": system_content}, *non_system]


def last_user_query(messages: list[dict[str, str]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content") or ""
    return ""
