/**
 * Start FastAPI (uvicorn) from backend/ with a sensible Python interpreter.
 * Prefers backend/.venv when present; otherwise `python` (Windows) or `python3`.
 */

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const backend = path.join(path.resolve(__dirname, ".."), "backend");

const venvWin = path.join(backend, ".venv", "Scripts", "python.exe");
const venvUnix = path.join(backend, ".venv", "bin", "python");

function pickPython() {
  if (process.platform === "win32" && fs.existsSync(venvWin)) {
    return { cmd: venvWin, shell: false };
  }
  if (process.platform !== "win32" && fs.existsSync(venvUnix)) {
    return { cmd: venvUnix, shell: false };
  }
  if (process.platform === "win32") {
    return { cmd: "python", shell: true };
  }
  return { cmd: "python3", shell: false };
}

const { cmd, shell } = pickPython();
const args = [
  "-m",
  "uvicorn",
  "app.main:app",
  "--reload",
  "--host",
  "127.0.0.1",
  "--port",
  "8000",
];

const child = spawn(cmd, args, {
  cwd: backend,
  stdio: "inherit",
  shell,
});

child.on("exit", (code, signal) => {
  if (signal) process.exit(1);
  process.exit(code ?? 0);
});
