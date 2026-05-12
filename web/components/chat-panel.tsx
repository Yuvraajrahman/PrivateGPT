"use client";

import { useChat } from "@ai-sdk/react";
import type { UIMessage } from "ai";
import { useCallback, useEffect, useRef, useState } from "react";

import { BackendConnectionBanner } from "@/components/backend-connection-banner";

function renderPart(part: UIMessage["parts"][number], key: string) {
  switch (part.type) {
    case "text":
      return (
        <div key={key} className="whitespace-pre-wrap leading-relaxed">
          {part.text}
        </div>
      );
    case "source-document":
      return (
        <div
          key={key}
          className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs text-[var(--muted)]"
        >
          <span className="font-mono text-[var(--accent)]">source</span>{" "}
          {part.sourceId ? `Source · ${part.sourceId.slice(0, 8)}` : "Source"}
        </div>
      );
    default:
      return null;
  }
}

function TypingIndicator() {
  return (
    <div className="flex max-w-[min(100%,720px)] items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--bg)]/90 px-4 py-3 text-sm">
      <div className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--muted)] [animation-delay:-0.2s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--muted)] [animation-delay:-0.1s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--muted)]" />
      </div>
      <span className="text-[var(--muted)]">YuviGPT is thinking…</span>
    </div>
  );
}

export function ChatPanel() {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const { messages, sendMessage, status, stop, error } = useChat();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const busy = status === "streaming" || status === "submitted";

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const text = input.trim();
      if (!text || busy) return;
      setInput("");
      await sendMessage({ text });
    },
    [input, busy, sendMessage],
  );

  return (
    <div className="flex h-[min(88vh,900px)] flex-col rounded-2xl border border-[var(--border)] bg-[var(--surface)]/80 shadow-2xl shadow-black/40 backdrop-blur">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Chat</h2>
          <p className="text-sm text-[var(--muted)]">
            Streaming via AI SDK · RAG runs on your FastAPI backend
          </p>
        </div>
        <div className="flex items-center gap-2">
          {busy ? (
            <button
              type="button"
              onClick={() => void stop()}
              className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--muted)] hover:border-red-500/50 hover:text-red-300"
            >
              Stop
            </button>
          ) : null}
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-medium ${
              busy
                ? "bg-[var(--accent-dim)] text-[var(--accent)]"
                : "bg-[var(--border)] text-[var(--muted)]"
            }`}
          >
            {status}
          </span>
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
        <BackendConnectionBanner />
        {messages.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            Ingest your portfolio docs into the API, then ask questions. Citations
            appear as source cards when retrieval finds chunks.
          </p>
        ) : null}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[min(100%,720px)] rounded-2xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-[var(--accent-dim)] text-[var(--text)]"
                  : "border border-[var(--border)] bg-[var(--bg)]/90"
              }`}
            >
              <div className="mb-1 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                {m.role}
              </div>
              {m.parts.map((part, i) =>
                renderPart(part, `${m.id}-${i}-${part.type}`),
              )}
            </div>
          </div>
        ))}
        {busy ? (
          <div className="flex justify-start">
            <TypingIndicator />
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      {error ? (
        <div className="border-t border-red-500/30 bg-red-950/40 px-5 py-2 text-sm text-red-200">
          {error.message}
        </div>
      ) : null}

      <form
        onSubmit={(e) => void onSubmit(e)}
        className="border-t border-[var(--border)] p-4"
      >
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message YuviGPT…"
            rows={2}
            className="min-h-[52px] flex-1 resize-y rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm outline-none ring-[var(--accent)]/30 placeholder:text-[var(--muted)] focus:border-[var(--accent)]/50 focus:ring-2"
            disabled={busy}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void onSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="self-end rounded-xl bg-[var(--accent)] px-5 py-2 text-sm font-semibold text-[var(--bg)] disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
