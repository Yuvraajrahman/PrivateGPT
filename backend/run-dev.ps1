# Start the YuviGPT FastAPI server (port 8000). LM Studio stays on :1234 — run it separately.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}

python -c "import uvicorn" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "uvicorn not found. Create a venv and install deps:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

Write-Host "Starting RAG API at http://127.0.0.1:8000 (ensure LM Studio is running if using OPENAI_BASE_URL)..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
