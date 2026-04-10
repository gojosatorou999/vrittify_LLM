# start_api.ps1 — Start the FastAPI server
# Usage: .\start_api.ps1

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=============================================="
Write-Host " Starting FastAPI LLM API server"
Write-Host " Port   : 8000 (fallback: 8001, 8002)"
Write-Host " Docs   : http://localhost:8000/docs"
Write-Host "=============================================="

py -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
