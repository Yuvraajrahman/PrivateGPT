export const maxDuration = 60;

export async function POST(req: Request) {
  const base = process.env.RAG_BACKEND_URL;
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

  const body = await req.text();
  const url = `${base.replace(/\/$/, "")}/v1/chat`;
  const upstream = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": req.headers.get("content-type") || "application/json",
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
      connection: "keep-alive",
    },
  });
}
