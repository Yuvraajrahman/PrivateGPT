/**
 * One-shot local chatbot: FastAPI (:8000) + Next.js (dev server, usually :3000).
 * Does not start cloudflared (use `npm run dev` for a public tunnel to the API).
 *
 * Usage (repo root):
 *   npm run start:chatbot
 *   node scripts/start-local-chatbot.cjs
 */

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const web = path.join(root, "web");
const backend = path.join(root, "backend");

function die(msg) {
  console.error(`[start-local-chatbot] ${msg}`);
  process.exit(1);
}

function warn(msg) {
  console.warn(`[start-local-chatbot] ${msg}`);
}

function main() {
  if (!fs.existsSync(path.join(root, "node_modules"))) {
    die('Run "npm install" at the repo root first.');
  }
  if (!fs.existsSync(path.join(web, "node_modules"))) {
    die('Run "npm install --prefix web" (or "npm install" from web/) first.');
  }
  if (!fs.existsSync(path.join(root, "node_modules", "concurrently"))) {
    die('Missing concurrently — run "npm install" at the repo root.');
  }

  if (!fs.existsSync(path.join(backend, ".env"))) {
    warn(
      "No backend/.env — see repo .env.example, then create backend/.env (RAG_API_KEY, LLM settings).",
    );
  }
  if (!fs.existsSync(path.join(web, ".env.local"))) {
    warn('No web/.env.local — copy web/.env.local.example; RAG_API_KEY must match backend/.env.');
  }

  const venvPy =
    process.platform === "win32"
      ? path.join(backend, ".venv", "Scripts", "python.exe")
      : path.join(backend, ".venv", "bin", "python");
  if (!fs.existsSync(venvPy)) {
    warn(
      "No backend/.venv detected — dev-backend will fall back to system Python; create a venv if imports fail.",
    );
  }

  console.log(`
>> PrivateGPT — local chatbot
>> Starting API + web. Open the Local URL printed by Next.js (often http://localhost:3000).
>> For local LLM: start LM Studio → load model → server at http://127.0.0.1:1234/v1
>> Remote API URL for Vercel: use "npm run dev" (includes cloudflared → :8000).
`);

  const child = spawn("npm", ["run", "dev:local"], {
    cwd: root,
    stdio: "inherit",
    shell: true,
  });

  child.on("error", (err) => {
    die(`Failed to spawn npm: ${err.message}`);
  });

  child.on("exit", (code, signal) => {
    if (signal) process.exit(1);
    process.exit(code ?? 0);
  });
}

main();
