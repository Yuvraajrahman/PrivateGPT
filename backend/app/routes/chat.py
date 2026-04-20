from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.chat_logic import build_llm_messages, last_user_query
from app.rag.llm_client import stream_llm
from app.rag.streaming import new_message_ids, sse_source_document, stream_ui_message
from app.schemas import normalize_messages

router = APIRouter(tags=["chat"])


@router.post("/v1/chat")
async def chat(request: Request) -> StreamingResponse:
    settings = request.app.state.settings
    retriever = request.app.state.retriever

    body = await request.json()
    messages = normalize_messages(body.get("messages") or [])
    query = last_user_query(messages)
    context_chunks = retriever.retrieve(query) if query else []

    source_events = [
        sse_source_document(
            c["id"],
            f"{c['metadata'].get('source', 'doc')} · {c['id'][:8]}",
        )
        for c in context_chunks
    ]

    llm_messages = build_llm_messages(messages, context_chunks)

    mid, tid = new_message_ids()
    token_stream = stream_llm(settings, llm_messages)

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
