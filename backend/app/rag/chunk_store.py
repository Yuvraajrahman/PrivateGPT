from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from threading import Lock

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class ChunkStore:
    """Persists dense vectors (Chroma) + sparse index (BM25) over the same chunk ids."""

    def __init__(
        self,
        persist_dir: Path,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._persist_dir = persist_dir
        self._lock = Lock()
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name="privategpt",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        self._chunk_ids: list[str] = []
        self._texts: list[str] = []
        self._metadatas: list[dict] = []
        self._bm25: BM25Okapi | None = None
        self._load_sidecar()

    def _sidecar_path(self) -> Path:
        return self._persist_dir / "bm25_sidecar.json"

    def _load_sidecar(self) -> None:
        path = self._sidecar_path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._chunk_ids = data.get("chunk_ids", [])
            self._texts = data.get("texts", [])
            self._metadatas = data.get("metadatas", [])
            if self._texts:
                tokens = [_tokenize(t) for t in self._texts]
                self._bm25 = BM25Okapi(tokens)
        except (json.JSONDecodeError, OSError):
            self._chunk_ids = []
            self._texts = []
            self._metadatas = []
            self._bm25 = None

    def _save_sidecar(self) -> None:
        path = self._sidecar_path()
        path.write_text(
            json.dumps(
                {
                    "chunk_ids": self._chunk_ids,
                    "texts": self._texts,
                    "metadatas": self._metadatas,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _rebuild_bm25(self) -> None:
        if not self._texts:
            self._bm25 = None
            return
        tokens = [_tokenize(t) for t in self._texts]
        self._bm25 = BM25Okapi(tokens)

    def clear(self) -> None:
        with self._lock:
            self._client.delete_collection("privategpt")
            self._collection = self._client.get_or_create_collection(
                name="privategpt",
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            self._chunk_ids = []
            self._texts = []
            self._metadatas = []
            self._bm25 = None
            self._save_sidecar()

    def add_text(
        self,
        text: str,
        source: str,
        extra_metadata: dict | None = None,
    ) -> int:
        chunks = self._splitter.split_text(text)
        if not chunks:
            return 0
        added = 0
        with self._lock:
            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict] = []
            for ch in chunks:
                cid = str(uuid.uuid4())
                meta = {"source": source, **(extra_metadata or {})}
                ids.append(cid)
                documents.append(ch)
                metadatas.append(meta)
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
            self._chunk_ids.extend(ids)
            self._texts.extend(documents)
            self._metadatas.extend(metadatas)
            self._rebuild_bm25()
            self._save_sidecar()
            added = len(ids)
        return added

    @property
    def chunk_count(self) -> int:
        return len(self._chunk_ids)

    def get_texts_for_ids(self, ids: list[str]) -> dict[str, tuple[str, dict]]:
        out: dict[str, tuple[str, dict]] = {}
        for i, cid in enumerate(self._chunk_ids):
            if cid in ids:
                out[cid] = (self._texts[i], self._metadatas[i])
        return out

    def dense_search(self, query: str, k: int) -> list[tuple[str, float]]:
        if not self._chunk_ids:
            return []
        n = min(k, len(self._chunk_ids))
        res = self._collection.query(query_texts=[query], n_results=max(1, n))
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        order: list[tuple[str, float]] = []
        for cid, d in zip(ids, dists, strict=False):
            order.append((cid, float(d)))
        return order

    def sparse_top(self, query: str, k: int) -> list[tuple[str, float]]:
        if not self._bm25 or not self._chunk_ids:
            return []
        q = _tokenize(query)
        scores = self._bm25.get_scores(q)
        ranked = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:k]
        return [(self._chunk_ids[i], float(scores[i])) for i in ranked]
