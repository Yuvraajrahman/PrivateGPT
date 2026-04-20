from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import CrossEncoder

from app.config import Settings
from app.rag.chunk_store import ChunkStore


@lru_cache(maxsize=1)
def _cross_encoder(model_name: str) -> CrossEncoder:
    return CrossEncoder(model_name)


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[str]:
    scores: dict[str, float] = {}
    for ids in ranked_lists:
        for rank, doc_id in enumerate(ids, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)


class HybridRetriever:
    def __init__(self, store: ChunkStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    def retrieve(self, query: str) -> list[dict]:
        if not query.strip() or self._store.chunk_count == 0:
            return []

        dense = self._store.dense_search(query, self._settings.k_dense)
        sparse = self._store.sparse_top(query, self._settings.k_sparse)

        dense_ids = [d for d, _ in dense]
        sparse_ids = [d for d, _ in sparse]
        fused_ids = reciprocal_rank_fusion(
            [dense_ids, sparse_ids],
            k=self._settings.rrf_k,
        )[: self._settings.k_fused]

        texts_map = self._store.get_texts_for_ids(fused_ids)
        pairs: list[list[str]] = []
        valid_ids: list[str] = []
        for cid in fused_ids:
            if cid not in texts_map:
                continue
            text, _ = texts_map[cid]
            pairs.append([query, text])
            valid_ids.append(cid)

        if not pairs:
            return []

        ce = _cross_encoder(self._settings.cross_encoder_model)
        ce_scores = ce.predict(pairs, show_progress_bar=False)
        order = np.argsort(ce_scores)[::-1][: self._settings.k_final]

        results: list[dict] = []
        for idx in order:
            cid = valid_ids[int(idx)]
            text, meta = texts_map[cid]
            results.append(
                {
                    "id": cid,
                    "text": text,
                    "metadata": meta,
                    "cross_encoder_score": float(ce_scores[int(idx)]),
                }
            )
        return results
