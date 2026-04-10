# start_llama.ps1 — Start the llama.cpp server
# Usage: .\start_llama.ps1

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LlamaServer = Join-Path $ProjectRoot "llama-cpp\llama-server.exe"
$Model = Join-Path $ProjectRoot "models\phi3.gguf"

# Find free port starting from 8080
$Port = 8080
foreach ($p in 8080, 8081, 8082) {
    $connection = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if (-not $connection) {
        $Port = $p
        break
    }
    Write-Host "Port $p is in use, trying next..."
}

Write-Host "=============================================="
Write-Host " Starting llama.cpp server"
Write-Host " Model  : $Model"
Write-Host " Port   : $Port"
Write-Host " Context: 4096"
Write-Host "=============================================="

if (-not (Test-Path $LlamaServer)) {
    Write-Host "ERROR: llama-server.exe not found at $LlamaServer"
    exit 1
}
if (-not (Test-Path $Model)) {
    Write-Host "ERROR: Model not found at $Model"
    exit 1
}

& $LlamaServer -m $Model --port $Port -c 4096 -ngl 0 --threads 6
