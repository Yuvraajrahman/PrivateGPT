// Wall-clock limit includes the entire streamed response. 60s is easy to exceed
// with local LLMs + RAG; Hobby allows up to 300s (see Vercel function duration docs).
import dns from "node:dns";

import {
  hintForBackendFetchFailure,
  isLocalhostBackendUrl,
  isRunningOnVercel,
  normalizeRagBackendBase,
} from "@/lib/rag-backend";

// Vercel → home tunnels sometimes fail on IPv6; prefer IPv4 for outbound fetch.
dns.setDefaultResultOrder("ipv4first");

export const maxDuration = 300;
export const dynamic = "force-dynamic";

function describeFetchFailure(e: unknown): string {
  if (!(e instanceof Error)) return String(e);
  const parts = [e.message];
  const c = e.cause;
  if (c instanceof Error) parts.push(`cause: ${c.message}`);
  else if (typeof c === "object" && c !== null && "code" in c)
    parts.push(`code: ${String((c as { code?: unknown }).code)}`);
  return parts.join(" · ");
}

export async function POST(req: Request) {
  const base = process.env.RAG_BACKEND_URL?.trim();
  const apiKey = process.env.RAG_API_KEY;
  if (!base) {
    return new Response(
      JSON.stringify({
        error:
          "RAG_BACKEND_URL is not set. Add it in Vercel project env (or web/.env.local) to your reachable FastAPI URL.",
      }),
      {
        status: 500,
        headers: { "content-type": "application/json" },
      },
    );
  }
  if (!apiKey) {
    return new Response(
      JSON.stringify({
        error:
          "RAG_API_KEY is not set. Add it in Vercel project env (or web/.env.local) to match backend RAG_API_KEY.",
      }),
      {
        status: 500,
        headers: { "content-type": "application/json" },
      },
    );
  }

  const backendBase = normalizeRagBackendBase(base);
  if (isRunningOnVercel() && isLocalhostBackendUrl(backendBase)) {
    return new Response(
      JSON.stringify({
        error:
          "RAG_BACKEND_URL points to localhost, which Vercel cannot reach. In Vercel → Settings → Environment Variables, set RAG_BACKEND_URL to your public HTTPS tunnel (e.g. cloudflared) that forwards to FastAPI on port 8000, apply to Production, then redeploy.",
      }),
      {
        status: 503,
        headers: { "content-type": "application/json" },
      },
    );
  }

  const body = await req.text();
  const url = `${backendBase}/v1/chat`;
  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: "POST",
      headers: {
        "content-type": req.headers.get("content-type") || "application/json",
        authorization: `Bearer ${apiKey}`,
      },
      body,
    });
  } catch (e) {
    const detail = describeFetchFailure(e);
    const extra = hintForBackendFetchFailure(detail);
    return new Response(
      JSON.stringify({
        error: `Cannot reach the RAG API at ${url} (${detail}). Hosted (Vercel): your PC must expose FastAPI over HTTPS (e.g. cloudflared) with RAG_BACKEND_URL set to that URL in Vercel env; keep the tunnel + uvicorn + LM Studio running. Quick trycloudflare URLs stop working when cloudflared exits or the URL changes—use a named tunnel or stable ingress. Local dev: RAG_BACKEND_URL=http://127.0.0.1:8000 with FastAPI on 8000.${extra ? ` ${extra}` : ""}`,
      }),
      {
        status: 502,
        headers: { "content-type": "application/json" },
      },
    );
  }

  if (!upstream.ok) {
    const text = await upstream.text();
    return new Response(text || upstream.statusText, {
      status: upstream.status,
    });
  }

  if (!upstream.body) {
    return new Response("Upstream returned empty body", { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "content-type":
        upstream.headers.get("content-type") || "text/event-stream",
      "x-vercel-ai-ui-message-stream":
        upstream.headers.get("x-vercel-ai-ui-message-stream") || "v1",
      "cache-control": "no-cache",
    },
  });
}
