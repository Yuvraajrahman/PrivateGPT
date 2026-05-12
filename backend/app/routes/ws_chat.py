from __future__ import annotations

import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from app.chat_logic import (
    apply_private_redaction,
    build_llm_messages,
    last_user_query,
    scrub_git_urls_from_stream,
)
from app.rag.llm_client import stream_llm
from app.schemas import normalize_messages
from app.security import require_api_key_websocket

router = APIRouter(tags=["chat"])


@router.websocket("/v1/chat/ws")
async def chat_websocket(websocket: WebSocket, request: Request) -> None:
    """WebSocket alternative: JSON messages with {type:'delta', text} then {type:'done'}."""
    await require_api_key_websocket(websocket, request)
    await websocket.accept()
    settings = request.app.state.settings
    retriever = request.app.state.retriever
    persona_text = getattr(request.app.state, "persona_text", "")
    try:
        payload_raw = await websocket.receive_text()
        payload = json.loads(payload_raw)
        messages = normalize_messages(payload.get("messages") or [])

        query = last_user_query(messages)
        context_chunks = retriever.retrieve(query) if query else []
        handles = settings.redact_handle_list
        llm_messages = build_llm_messages(
            messages,
            context_chunks,
            persona_text=persona_text,
            redact_handles=handles,
        )

        await websocket.send_json(
            {
                "type": "meta",
                "sources": [
                    {
                        "id": c["id"],
                        "preview": apply_private_redaction(
                            (c.get("text") or ""),
                            handles,
                        )[:240],
                    }
                    for c in context_chunks
                ],
            }
        )

        async for piece in scrub_git_urls_from_stream(
            stream_llm(settings, llm_messages),
            handles,
        ):
            if piece:
                await websocket.send_json({"type": "delta", "text": piece})
        await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"type": "error", "message": str(exc)})
