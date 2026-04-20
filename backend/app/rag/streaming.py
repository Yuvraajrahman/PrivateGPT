from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator


def _sse(data: str) -> str:
    return f"data: {data}\n\n"


async def stream_ui_message(
    message_id: str,
    text_block_id: str,
    token_stream: AsyncIterator[str],
    source_events: list[str] | None = None,
) -> AsyncIterator[str]:
    """Yield AI SDK UI message stream (SSE) lines."""
    yield _sse(json.dumps({"type": "start", "messageId": message_id}))
    if source_events:
        for ev in source_events:
            yield ev
    yield _sse(json.dumps({"type": "text-start", "id": text_block_id}))
    async for token in token_stream:
        if not token:
            continue
        yield _sse(
            json.dumps({"type": "text-delta", "id": text_block_id, "delta": token})
        )
    yield _sse(json.dumps({"type": "text-end", "id": text_block_id}))
    yield _sse(json.dumps({"type": "finish"}))
    yield _sse("[DONE]")


def new_message_ids() -> tuple[str, str]:
    mid = f"msg_{uuid.uuid4().hex}"
    tid = f"txt_{uuid.uuid4().hex}"
    return mid, tid


def sse_source_document(source_id: str, title: str) -> str:
    payload = {
        "type": "source-document",
        "sourceId": source_id,
        "mediaType": "file",
        "title": title[:500],
    }
    return _sse(json.dumps(payload))
