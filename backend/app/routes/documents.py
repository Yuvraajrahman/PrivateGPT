from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
) -> dict:
    store = request.app.state.chunk_store
    raw = await file.read()
    text = raw.decode("utf-8", errors="replace")
    source = file.filename or "upload"
    n = store.add_text(text, source=source, extra_metadata={"kind": "upload"})
    return {"chunks_added": n, "source": source, "total_chunks": store.chunk_count}


@router.post("/clear")
async def clear_documents(request: Request) -> dict:
    store = request.app.state.chunk_store
    store.clear()
    return {"ok": True, "total_chunks": 0}
