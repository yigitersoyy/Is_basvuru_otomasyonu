$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Test-Path .env)) {
    python scripts/configure.py
    if ($LASTEXITCODE -ne 0) { throw 'Configuration failed' }
}
docker compose up -d --build --wait
if ($LASTEXITCODE -ne 0) { throw 'Stack startup failed; inspect docker compose logs' }
Write-Host 'Workspace: http://localhost:8080'
Write-Host 'API: http://localhost:8000/docs | n8n: http://localhost:5678 | Test mailbox: http://localhost:8025'
