// Wall-clock limit includes the entire streamed response. 60s is easy to exceed
// with local LLMs + RAG; Hobby allows up to 300s (see Vercel function duration docs).
export const maxDuration = 300;
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const base = process.env.RAG_BACKEND_URL;
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

  const body = await req.text();
  const url = `${base.replace(/\/$/, "")}/v1/chat`;
  const upstream = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": req.headers.get("content-type") || "application/json",
      authorization: `Bearer ${apiKey}`,
    },
    body,
  });

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
