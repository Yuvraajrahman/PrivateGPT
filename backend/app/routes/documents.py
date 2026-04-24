from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.security import require_api_key

router = APIRouter(prefix="/v1/documents", tags=["documents"])

@router.get("/stats")
async def document_stats(
    request: Request,
    _auth: None = Depends(require_api_key),
) -> dict:
    store = request.app.state.chunk_store
    return {
        "total_chunks": store.chunk_count,
        "sources": store.sources(),
    }


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    _auth: None = Depends(require_api_key),
) -> dict:
    store = request.app.state.chunk_store
    raw = await file.read()
    if len(raw) > 10_000_000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB).",
        )
    text = raw.decode("utf-8", errors="replace")
    source = file.filename or "upload"
    n = store.add_text(text, source=source, extra_metadata={"kind": "upload"})
    return {"chunks_added": n, "source": source, "total_chunks": store.chunk_count}


@router.post("/clear")
async def clear_documents(
    request: Request,
    _auth: None = Depends(require_api_key),
) -> dict:
    store = request.app.state.chunk_store
    store.clear()
    return {"ok": True, "total_chunks": 0}
