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
