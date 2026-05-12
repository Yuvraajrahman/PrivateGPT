from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.chat_logic import build_llm_messages, last_user_query, scrub_git_urls_from_stream
from app.rag.llm_client import stream_llm
from app.rag.streaming import new_message_ids, sse_source_document, stream_ui_message
from app.schemas import normalize_messages
from app.security import require_api_key

router = APIRouter(tags=["chat"])


@router.post("/v1/chat")
async def chat(
    request: Request,
    _auth: None = Depends(require_api_key),
) -> StreamingResponse:
    settings = request.app.state.settings
    retriever = request.app.state.retriever
    persona_text = getattr(request.app.state, "persona_text", "")

    body = await request.json()
    messages = normalize_messages(body.get("messages") or [])
    query = last_user_query(messages)
    context_chunks = retriever.retrieve(query) if query else []

    source_events = [
        sse_source_document(
            c["id"],
            f"Source · {c['id'][:8]}",
        )
        for c in context_chunks
    ]

    handles = settings.redact_handle_list
    llm_messages = build_llm_messages(
        messages,
        context_chunks,
        persona_text=persona_text,
        redact_handles=handles,
    )

    mid, tid = new_message_ids()
    token_stream = scrub_git_urls_from_stream(
        stream_llm(settings, llm_messages),
        handles,
    )

    async def event_stream():
        async for line in stream_ui_message(mid, tid, token_stream, source_events):
            yield line

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
