from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings

router = APIRouter(prefix="/v1/notion", tags=["notion"])


def _flatten_notion_blocks(blocks: list[dict]) -> str:
    parts: list[str] = []
    for b in blocks:
        t = b.get("type")
        if not t:
            continue
        payload = b.get(t) or {}
        rich = payload.get("rich_text") or []
        line = "".join(
            (x.get("plain_text") or "") for x in rich if isinstance(x, dict)
        )
        if line.strip():
            parts.append(line)
    return "\n".join(parts)


@router.post("/sync")
async def sync_notion_page(request: Request) -> dict:
    settings = get_settings()
    if not settings.notion_token or not settings.notion_page_id:
        raise HTTPException(
            status_code=400,
            detail="Set NOTION_TOKEN and NOTION_PAGE_ID to enable Notion sync.",
        )

    from notion_client import Client

    client = Client(auth=settings.notion_token)
    page_id = settings.notion_page_id
    blocks: list[dict] = []
    cursor = None
    while True:
        res = client.blocks.children.list(block_id=page_id, start_cursor=cursor)
        blocks.extend(res.get("results") or [])
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")

    text = _flatten_notion_blocks(blocks)
    if not text.strip():
        return {"chunks_added": 0, "message": "No text extracted from Notion page."}

    store = request.app.state.chunk_store
    n = store.add_text(
        text,
        source=f"notion:{settings.notion_page_id}",
        extra_metadata={"kind": "notion"},
    )
    return {"chunks_added": n, "total_chunks": store.chunk_count}
