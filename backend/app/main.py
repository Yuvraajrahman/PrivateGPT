from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.rag.chunk_store import ChunkStore
from app.rag.retriever import HybridRetriever
from app.routes import chat, documents, health, notion, ws_chat


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
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PrivateGPT",
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
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(ws_chat.router)
    app.include_router(documents.router)
    app.include_router(notion.router)
    return app


app = create_app()
