import { ChatPanel } from "@/components/chat-panel";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-12 md:px-8">
      <section className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
          Self-hosted · Hybrid RAG
        </p>
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
          PrivateGPT
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

      <ChatPanel />

      <footer className="border-t border-[var(--border)] pt-8 text-center text-xs text-[var(--muted)]">
        Set <code className="text-[var(--accent)]">RAG_BACKEND_URL</code> on Vercel to
        a reachable URL for your home API (for example a Cloudflare Tunnel). Never
        commit secrets.
      </footer>
    </main>
  );
}
