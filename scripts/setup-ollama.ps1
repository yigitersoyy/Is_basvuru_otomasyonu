param([string]$Model = 'qwen3.5:9b', [switch]$Install)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
# Native Ollama handles Windows GPU discovery; never assume a particular VRAM size.
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    if ($LASTEXITCODE -ne 0) { throw 'GPU inspection failed; resolve the driver issue first.' }
} else { Write-Warning 'NVIDIA driver utility unavailable. GPU/VRAM is unverified; CPU inference may be used.' }
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (!$ollama) {
    if (!$Install) { throw 'Ollama is not installed. Run this script with -Install to install the signed winget package.' }
    if (!(Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Install Windows App Installer (winget), then retry.' }
    winget install --id Ollama.Ollama --exact --source winget --accept-source-agreements --accept-package-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'Ollama installation failed. No alternative model or API was selected.' }
    $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (!(Test-Path $candidate)) { throw 'Open a new terminal and rerun; Ollama executable is not yet on PATH.' }
    $ollama = Get-Item $candidate
}
$exe = if ($ollama.Source) { $ollama.Source } else { $ollama.FullName }
$env:OLLAMA_NO_CLOUD = '1'
[Environment]::SetEnvironmentVariable('OLLAMA_NO_CLOUD', '1', 'User')
Write-Host 'Restart any previously running Ollama app to apply the persisted local-only setting.'
try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' | Out-Null }
catch {
    Start-Process $exe -ArgumentList 'serve' -WindowStyle Hidden
    $ready = $false
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' | Out-Null; $ready=$true; break } catch {}
    }
    if (!$ready) { throw 'Ollama did not become ready. Inspect local Ollama logs.' }
}
# Pull validates that the exact requested tag exists. Failure never substitutes another model.
& $exe pull $Model
if ($LASTEXITCODE -ne 0) { throw "Requested artifact $Model is unavailable; check the official Ollama library. No fallback used." }
python scripts/verify_model.py --model $Model
if ($LASTEXITCODE -ne 0) { throw 'Model validation failed. Do not enable inference until resolved.' }
if (!(Test-Path .env)) {
    python scripts/configure.py
    if ($LASTEXITCODE -ne 0) { throw 'Local configuration creation failed.' }
}
$configPath = Join-Path (Get-Location) '.env'
$config = [IO.File]::ReadAllText($configPath)
foreach ($entry in @(@('OLLAMA_URL', 'http://host.docker.internal:11434'), @('OLLAMA_MODEL', $Model))) {
    $pattern = '(?m)^' + $entry[0] + '=.*$'
    $line = $entry[0] + '=' + $entry[1]
    if ([regex]::IsMatch($config, $pattern)) { $config = [regex]::Replace($config, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $line }) }
    else { $config += "`n" + $line + "`n" }
}
[IO.File]::WriteAllText($configPath, $config, (New-Object Text.UTF8Encoding($false)))
Write-Host 'Saved verified model and native Ollama connection in private .env; existing secrets were preserved.'
Write-Host 'Recreate api. Keep Ollama bound to loopback; do not expose its port to the LAN. Verify Docker-to-host connectivity locally.'
