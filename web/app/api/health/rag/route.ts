import dns from "node:dns";

import {
  isLocalhostBackendUrl,
  isRunningOnVercel,
  normalizeRagBackendBase,
} from "@/lib/rag-backend";

dns.setDefaultResultOrder("ipv4first");

export const dynamic = "force-dynamic";

/**
 * GET /api/health/rag — checks whether this deployment can reach FastAPI at RAG_BACKEND_URL.
 * Does not send your API key; backend /health is unauthenticated.
 */
export async function GET() {
  const raw = process.env.RAG_BACKEND_URL?.trim();
  if (!raw) {
    return Response.json(
      {
        ok: false,
        step: "env",
        detail: "RAG_BACKEND_URL is not set in this environment.",
      },
      { status: 500 },
    );
  }

  const base = normalizeRagBackendBase(raw);
  if (isRunningOnVercel() && isLocalhostBackendUrl(base)) {
    return Response.json(
      {
        ok: false,
        step: "localhost_on_vercel",
        detail:
          "RAG_BACKEND_URL points to localhost. Vercel cannot reach your PC. Set it to your HTTPS tunnel URL (Production env) and redeploy.",
      },
      { status: 503 },
    );
  }

  const healthUrl = `${base}/health`;
  try {
    const upstream = await fetch(healthUrl, {
      method: "GET",
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
    const text = await upstream.text();
    if (!upstream.ok) {
      return Response.json(
        {
          ok: false,
          step: "upstream_http",
          healthUrl,
          status: upstream.status,
          bodyPreview: text.slice(0, 200),
        },
        { status: 502 },
      );
    }
    return Response.json({
      ok: true,
      healthUrl,
      upstream: text.slice(0, 200),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    const cause =
      e instanceof Error && e.cause instanceof Error
        ? e.cause.message
        : undefined;
    return Response.json(
      {
        ok: false,
        step: "fetch_failed",
        healthUrl,
        error: msg,
        cause,
        hint:
          "Keep cloudflared (or your tunnel) + uvicorn on the same machine. Quick trycloudflare URLs change when cloudflared restarts—update Vercel RAG_BACKEND_URL and redeploy.",
      },
      { status: 502 },
    );
  }
}
