import { ChatPanel } from "@/components/chat-panel";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-12 md:px-8">
      <section className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
          Self-hosted · Hybrid RAG
        </p>
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
          YuviGPT
        </h1>
        <p className="max-w-2xl text-lg text-[var(--muted)]">
          Chat UI for your FastAPI stack: BM25 + dense retrieval, cross-encoder
          re-ranking, and pluggable LLMs (LM Studio, Ollama, or any OpenAI-compatible
          endpoint). Deploy this interface on Vercel; keep inference and documents on
          your PC.
        </p>
        <ul className="grid gap-3 text-sm text-[var(--muted)] md:grid-cols-2">
          <li className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <span className="font-medium text-[var(--text)]">Backend</span> — Python,
            FastAPI, Chroma, LangChain text splitters, optional Notion sync.
          </li>
          <li className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <span className="font-medium text-[var(--text)]">Frontend</span> — Next.js,
            Vercel AI SDK streaming (SSE). Optional WebSocket at{" "}
            <code className="text-[var(--accent)]">/v1/chat/ws</code>.
          </li>
        </ul>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)]/60 p-5 md:col-span-2">
          <h2 className="text-base font-semibold tracking-tight">How it works</h2>
          <ol className="mt-3 space-y-2 text-sm text-[var(--muted)]">
            <li>
              <span className="font-medium text-[var(--text)]">1) Ingest</span> — your
              portfolio content is chunked and embedded, then stored in Chroma.
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">2) Retrieve</span> — for
              each question, YuviGPT runs hybrid search (BM25 + dense) to find the most
              relevant chunks.
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">3) Re-rank</span> — a
              cross-encoder reorders results for better precision.
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">4) Generate</span> — the
              LLM answers using the retrieved context and streams tokens live to the UI.
            </li>
          </ol>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)]/60 p-5">
          <h2 className="text-base font-semibold tracking-tight">Tech</h2>
          <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
            <li>
              <span className="font-medium text-[var(--text)]">UI</span> — Next.js 15 +
              React + Tailwind
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">Streaming</span> — Vercel
              AI SDK (SSE)
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">API</span> — FastAPI +
              httpx
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">RAG</span> — Chroma +
              BM25 + SentenceTransformers + cross-encoder rerank
            </li>
            <li>
              <span className="font-medium text-[var(--text)]">LLM</span> — LM Studio /
              Ollama (OpenAI-compatible)
            </li>
          </ul>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)]/60 p-5 md:col-span-3">
          <h2 className="text-base font-semibold tracking-tight">How I built it</h2>
          <p className="mt-3 text-sm text-[var(--muted)]">
            I wanted a portfolio assistant that runs locally and stays grounded in real
            data. So I built a hybrid RAG pipeline (dense + sparse) with re-ranking for
            accuracy, added streaming for a “feels instant” UI, and made the LLM backend
            pluggable so it works with local inference (LM Studio/Ollama) or any
            OpenAI-compatible server.
          </p>
        </div>
      </section>

      <ChatPanel />

      <footer className="border-t border-[var(--border)] pt-8 text-center text-xs text-[var(--muted)]">
        Set <code className="text-[var(--accent)]">RAG_BACKEND_URL</code> on Vercel to
        a reachable URL for your home API (for example a Cloudflare Tunnel). Never
        commit secrets.
      </footer>
    </main>
  );
}
