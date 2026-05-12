/**
 * Shared helpers for the Next.js → FastAPI proxy (RAG_BACKEND_URL).
 */

export function normalizeRagBackendBase(raw: string): string {
  let base = raw.trim().replace(/\/+$/, "");
  // Accept mistaken copy-paste: .../v1 → routes become .../v1/chat not .../v1/v1/chat
  if (base.endsWith("/v1")) {
    base = base.slice(0, -3).replace(/\/+$/, "");
  }
  return base;
}

export function isLocalhostBackendUrl(base: string): boolean {
  try {
    const { hostname } = new URL(base);
    return (
      hostname === "localhost" ||
      hostname === "127.0.0.1" ||
      hostname === "::1"
    );
  } catch {
    return false;
  }
}

export function isRunningOnVercel(): boolean {
  return process.env.VERCEL === "1";
}

/** Extra context when fetch() to the tunneled FastAPI fails (shown in API JSON errors). */
export function hintForBackendFetchFailure(detail: string): string | undefined {
  if (/ENOTFOUND|getaddrinfo/i.test(detail)) {
    return "Tunnel hostname no longer resolves. Quick trycloudflare URLs die when cloudflared stops or restarts. Run cloudflared again, copy the NEW https URL, set Vercel → Settings → Environment Variables → RAG_BACKEND_URL (Production), then Redeploy.";
  }
  if (/ECONNREFUSED|connection refused/i.test(detail)) {
    return "Connection refused at that host:port—confirm uvicorn is listening (e.g. http://127.0.0.1:8000) and the tunnel points to FastAPI, not LM Studio.";
  }
  return undefined;
}
