from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.rag.chunk_store import ChunkStore
from app.rag.retriever import HybridRetriever
from app.routes import chat, documents, health, notion, ws_chat
from app.security import FixedWindowRateLimiter, enforce_content_length, get_client_ip


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = ChunkStore(
        persist_dir=settings.chroma_path,
        embedding_model=settings.embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    app.state.chunk_store = store
    app.state.settings = settings
    app.state.retriever = HybridRetriever(store, settings)
    persona_path = Path(__file__).resolve().parents[1] / "persona.md"
    app.state.persona_text = (
        persona_path.read_text(encoding="utf-8") if persona_path.exists() else ""
    )

    # Auto-ingest the portfolio knowledge base (idempotent).
    portfolio_path = Path(__file__).resolve().parent / "PORTFOLIO.md"
    if portfolio_path.exists() and "PORTFOLIO.md" not in set(store.sources()):
        text = portfolio_path.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            store.add_text(
                text,
                source="PORTFOLIO.md",
                extra_metadata={"kind": "portfolio"},
            )

    # Simple in-memory rate limiting (per-process)
    app.state.ratelimit_chat = FixedWindowRateLimiter(window_seconds=60, max_requests=60)
    app.state.ratelimit_write = FixedWindowRateLimiter(window_seconds=60, max_requests=10)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    if not settings.rag_api_key:
        raise RuntimeError(
            "RAG_API_KEY is not set. Set it in backend/.env to enable minimum security."
        )
    app = FastAPI(
        title="YuviGPT",
        description="Self-hosted RAG backend with hybrid retrieval and pluggable LLMs.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def basic_limits(request, call_next):  # type: ignore[no-untyped-def]
        # Size limits (bytes)
        path = request.url.path
        if path == "/v1/chat":
            enforce_content_length(request, max_bytes=1_000_000)
            limiter = request.app.state.ratelimit_chat
            if not limiter.allow(f"{get_client_ip(request)}:chat"):
                from fastapi.responses import JSONResponse

                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        elif path.startswith("/v1/documents") or path.startswith("/v1/notion"):
            enforce_content_length(request, max_bytes=10_000_000)
            limiter = request.app.state.ratelimit_write
            if not limiter.allow(f"{get_client_ip(request)}:write"):
                from fastapi.responses import JSONResponse

                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        return await call_next(request)

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(ws_chat.router)
    app.include_router(documents.router)
    app.include_router(notion.router)
    return app


app = create_app()
