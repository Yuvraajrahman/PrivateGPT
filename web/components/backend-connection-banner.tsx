"use client";

import { useEffect, useState } from "react";

type RagHealthBad = {
  ok?: false;
  step?: string;
  detail?: string;
  hint?: string;
  healthUrl?: string;
  error?: string;
  cause?: string;
};

export function BackendConnectionBanner() {
  const [bad, setBad] = useState<RagHealthBad | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const r = await fetch("/api/health/rag", { cache: "no-store" });
        const data = (await r.json()) as { ok?: boolean } & Record<string, unknown>;
        if (cancelled) return;
        if (data.ok === true) {
          setBad(null);
          return;
        }
        setBad(data as RagHealthBad);
      } catch {
        if (cancelled) return;
        setBad({
          detail: "Could not load /api/health/rag from this site.",
        });
      }
    }
    void check();
    const t = setInterval(check, 45_000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  if (!bad) return null;

  return (
    <div className="rounded-xl border border-amber-500/45 bg-amber-950/55 px-4 py-3 text-sm text-amber-50 shadow-lg shadow-black/20">
      <p className="font-semibold text-amber-100">
        This deployment cannot reach your FastAPI backend
      </p>
      {bad.detail ? (
        <p className="mt-2 text-xs leading-relaxed text-amber-50/95">
          {bad.detail}
        </p>
      ) : null}
      {bad.hint ? (
        <p className="mt-2 text-xs leading-relaxed text-amber-100/85">
          {bad.hint}
        </p>
      ) : null}
      {bad.error ? (
        <p className="mt-1 font-mono text-[11px] text-amber-200/90">
          {bad.error}
          {bad.cause ? ` · ${bad.cause}` : ""}
        </p>
      ) : null}
      {bad.healthUrl ? (
        <p className="mt-1 break-all font-mono text-[10px] text-amber-50/70">
          Tried: {bad.healthUrl}
        </p>
      ) : null}
      {bad.step ? (
        <p className="mt-1 text-[10px] uppercase tracking-wide text-amber-50/60">
          step: {bad.step}
        </p>
      ) : null}
      <p className="mt-3 text-xs text-amber-50/90">
        On the PC that runs the API: keep{" "}
        <code className="rounded bg-black/30 px-1 py-0.5">uvicorn</code> on{" "}
        <code className="rounded bg-black/30 px-1 py-0.5">0.0.0.0:8000</code>,
        keep your HTTPS tunnel (e.g. cloudflared) pointing at that port, then set
        Vercel Production{" "}
        <code className="rounded bg-black/30 px-1">RAG_BACKEND_URL</code> to the
        current tunnel URL and redeploy. Quick tunnel hostnames change when
        cloudflared restarts.
      </p>
      <a
        className="mt-2 inline-block text-xs font-medium text-amber-300 underline underline-offset-2 hover:text-amber-200"
        href="/api/health/rag"
        target="_blank"
        rel="noreferrer"
      >
        Open connection diagnostic (JSON)
      </a>
    </div>
  );
}
