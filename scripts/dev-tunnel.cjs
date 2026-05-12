/**
 * Start cloudflared quick tunnel to FastAPI (8000), unless SKIP_TUNNEL=1.
 * If cloudflared is missing, log and exit 0 so api + web still start.
 */

const { spawn } = require("node:child_process");

if (process.env.SKIP_TUNNEL === "1") {
  console.log("[tunnel] SKIP_TUNNEL=1 — cloudflared not started.");
  process.exit(0);
}

const child = spawn(
  "cloudflared",
  ["tunnel", "--url", "http://127.0.0.1:8000"],
  { stdio: "inherit", shell: true },
);

child.on("error", (err) => {
  console.error("[tunnel] Could not start cloudflared:", err.message);
  console.error(
    "[tunnel] Install cloudflared and add it to PATH, or run: SKIP_TUNNEL=1 npm run dev",
  );
  process.exit(0);
});

child.on("exit", (code, signal) => {
  if (signal) process.exit(1);
  process.exit(code ?? 0);
});
