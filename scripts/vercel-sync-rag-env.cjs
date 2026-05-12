/**
 * Push RAG_BACKEND_URL + RAG_API_KEY to the linked Vercel project (production + preview).
 *
 * Prereqs:
 *   1) npm install (repo root — installs devDependency "vercel")
 *   2) npm run vercel:link   (once — creates .vercel at repo root for web/; login if prompted)
 *   3) Copy web/.env.vercel.secrets.example → web/.env.vercel.secrets and fill values
 *   4) npm run vercel:sync-env
 *
 * Preview: the CLI needs a Git branch interactively; update Preview in the dashboard if needed,
 * or run `vercel env add ... preview` locally once. Production is enough for `npm run vercel:deploy`.
 */

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const web = path.join(root, "web");
const secretsPath = path.join(web, ".env.vercel.secrets");
const vercelDirWeb = path.join(web, ".vercel");
const vercelDirRoot = path.join(root, ".vercel");

function parseDotEnv(content) {
  /** @type {Record<string, string>} */
  const out = {};
  for (const line of content.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const eq = t.indexOf("=");
    if (eq === -1) continue;
    const k = t.slice(0, eq).trim();
    let v = t.slice(eq + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    out[k] = v;
  }
  return out;
}

function runVercelEnvAdd(name, target, args) {
  const vcJs = path.join(root, "node_modules", "vercel", "dist", "vc.js");
  if (!fs.existsSync(vcJs)) {
    console.error(
      `Missing ${path.relative(root, vcJs)} — run "npm install" at the repo root.`,
    );
    process.exit(1);
  }
  const r = spawnSync(
    process.execPath,
    [vcJs, "--cwd", "web", "env", "add", name, target, ...args],
    {
      cwd: root,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "pipe"],
      env: process.env,
    },
  );
  if (r.stdout) console.log(r.stdout.trimEnd());
  if (r.stderr) console.error(r.stderr.trimEnd());
  if (r.status !== 0) {
    process.exit(r.status ?? 1);
  }
}

function main() {
  if (!fs.existsSync(vercelDirRoot) && !fs.existsSync(vercelDirWeb)) {
    console.error(
      "Missing .vercel/ — run from repo root: npm run vercel:link",
    );
    process.exit(1);
  }
  if (!fs.existsSync(secretsPath)) {
    console.error(
      `Missing ${path.relative(root, secretsPath)} — copy web/.env.vercel.secrets.example and fill RAG_BACKEND_URL + RAG_API_KEY.`,
    );
    process.exit(1);
  }

  const raw = fs.readFileSync(secretsPath, "utf8");
  const env = parseDotEnv(raw);
  const backendUrl = (env.RAG_BACKEND_URL || "").trim().replace(/\/+$/, "");
  const apiKey = (env.RAG_API_KEY || "").trim();

  if (!backendUrl || !/^https?:\/\//i.test(backendUrl)) {
    console.error(
      "RAG_BACKEND_URL must be set to an http(s) URL (e.g. https://….trycloudflare.com, no trailing /v1).",
    );
    process.exit(1);
  }
  if (!apiKey) {
    console.error("RAG_API_KEY must be non-empty (match backend/.env).");
    process.exit(1);
  }
  if (backendUrl.includes("127.0.0.1") || backendUrl.includes("localhost")) {
    console.error(
      "RAG_BACKEND_URL points to localhost — Vercel cannot reach it. Use your cloudflared HTTPS URL.",
    );
    process.exit(1);
  }

  const targets = ["production"];

  for (const target of targets) {
    console.log(`\n→ ${target}: RAG_BACKEND_URL`);
    runVercelEnvAdd("RAG_BACKEND_URL", target, [
      "--yes",
      "--force",
      "--value",
      backendUrl,
    ]);
  }

  for (const target of targets) {
    console.log(`\n→ ${target}: RAG_API_KEY (sensitive)`);
    runVercelEnvAdd("RAG_API_KEY", target, [
      "--yes",
      "--force",
      "--sensitive",
      "--value",
      apiKey,
    ]);
  }

  console.log(
    "\nDone. Deploy so the new env is picked up: npm run vercel:deploy (or Redeploy in the Vercel dashboard).",
  );
}

main();
