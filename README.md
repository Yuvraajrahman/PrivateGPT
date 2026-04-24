# YuviGPT

Self-hosted RAG chatbot: **FastAPI** backend (hybrid BM25 + dense retrieval, cross-encoder re-ranking, Chroma, optional Notion ingest) and a **Next.js** web UI that streams with the **Vercel AI SDK** (SSE). LLMs are pluggable via **LM Studio** (OpenAI-compatible), **Ollama**, or any other server that speaks the same HTTP API.

Your documents and prompts stay on hardware you control; the UI can be deployed to Vercel while the API stays at home (exposed through a tunnel you trust).

## Architecture

- **Backend (`backend/`)**: `POST /v1/chat` returns an AI SDK UI message stream (`x-vercel-ai-ui-message-stream: v1`). `POST /v1/documents/upload` ingests files; `POST /v1/notion/sync` pulls a Notion page when configured. `WebSocket /v1/chat/ws` streams JSON deltas for non-SSE clients.
- **Frontend (`web/`)**: Next.js 15 + `@ai-sdk/react` `useChat`. `POST /api/chat` proxies to your FastAPI URL from the `RAG_BACKEND_URL` environment variable (so the browser never needs your home IP or CORS hacks when you use the proxy).

## Quick start (local)

### 1. LM Studio (your setup)

1. Load **Gemma** (or any model) and start the local server (default **OpenAI-compatible** base URL is usually `http://127.0.0.1:1234/v1`).
2. In LM Studio, note the **exact model id** shown for the API (use that for `CHAT_MODEL`).

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env: RAG_API_KEY, OPENAI_BASE_URL, CHAT_MODEL, LLM_PROVIDER=openai_compatible
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

First run will download embedding and cross-encoder models (SentenceTransformers).

### 3. Ingest a document

```bash
curl -F "file=@./notes.md" http://127.0.0.1:8000/v1/documents/upload
```

### 4. Frontend

```bash
cd web
cp ../.env.example .env.local
# Set: RAG_BACKEND_URL=http://127.0.0.1:8000 and RAG_API_KEY=...
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and chat.

## Deploy the UI on Vercel

1. Connect this repo and set the Vercel **Root Directory** to `web`.
2. Add environment variable **`RAG_BACKEND_URL`** to the **public URL** where your FastAPI instance is reachable (for a home PC, use something like Cloudflare Tunnel, Tailscale Funnel, or another HTTPS reverse proxy you control).
3. On the machine running FastAPI, set **`CORS_ORIGINS`** to include your Vercel origin (for example `https://your-app.vercel.app`) so browser clients can call the API if you ever point the frontend at the API directly.
4. Redeploy. Long generations may require a Vercel Pro plan or similar for higher function timeouts; `web/app/api/chat/route.ts` sets `maxDuration = 60`.

## Ollama instead of LM Studio

In `backend/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
```

## Notion

1. Create an integration token and share the target page with the integration.
2. Set `NOTION_TOKEN` and `NOTION_PAGE_ID` in `backend/.env`.
3. Call `POST http://127.0.0.1:8000/v1/notion/sync` to ingest that page’s text.

## Cloud models (OpenAI, Gemini, etc.)

Any provider with an **OpenAI-compatible** HTTP API works with `LLM_PROVIDER=openai_compatible` by pointing `OPENAI_BASE_URL` and `OPENAI_API_KEY` at that provider (including many gateways and proxies). Native Gemini SDK is not wired in this repo; use a compatibility layer or gateway if you need Gemini.

## Security notes

- Do not expose FastAPI to the open internet without TLS, authentication, and rate limiting if your documents are sensitive.
- The Vercel app only stores `RAG_BACKEND_URL` server-side for the proxy; keep API keys for cloud LLMs in backend env, not in the Next.js client.

## License

Use and modify for your own deployment.
