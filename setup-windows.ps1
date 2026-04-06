# KLOR Bridge Windows Setup Script
# Run in PowerShell as Administrator (for HID access)
#
# Usage: .\setup-windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== KLOR Bridge Windows Setup ===" -ForegroundColor Cyan
Write-Host ""

# ─── Check Python ─────────────────────────────────────────────────────────────

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

$pyVersion = & python --version 2>&1
Write-Host "Found $pyVersion" -ForegroundColor Green

# ─── Install Python dependencies ──────────────────────────────────────────────

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow

pip install hidapi openai pyyaml keyring sounddevice numpy aiohttp pyautogui pyperclip

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed" -ForegroundColor Red
    exit 1
}

Write-Host "Dependencies installed" -ForegroundColor Green

# ─── Create config directory ──────────────────────────────────────────────────

$configDir = Join-Path $env:USERPROFILE ".config\klor-bridge"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Host "Created config directory: $configDir" -ForegroundColor Green
} else {
    Write-Host "Config directory exists: $configDir" -ForegroundColor Green
}

# ─── Copy config files ────────────────────────────────────────────────────────

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridgeDir = Join-Path $scriptDir "bridge"

$configFiles = @("config.yml", "actions.yml", "prompts.yml", "lexicon.yml", "corrections.yml")

Write-Host ""
Write-Host "Copying config files..." -ForegroundColor Yellow

foreach ($file in $configFiles) {
    $src = Join-Path $bridgeDir $file
    $dst = Join-Path $configDir $file

    if (Test-Path $src) {
        if (Test-Path $dst) {
            Write-Host "  SKIP $file (already exists, won't overwrite)" -ForegroundColor DarkYellow
        } else {
            Copy-Item $src $dst
            Write-Host "  COPY $file" -ForegroundColor Green
        }
    } else {
        Write-Host "  WARN $file not found in bridge/" -ForegroundColor DarkYellow
    }
}

# Copy Windows bridge script
$bridgeSrc = Join-Path $bridgeDir "klor-bridge-windows.py"
$bridgeDst = Join-Path $configDir "klor-bridge-windows.py"

if (Test-Path $bridgeSrc) {
    Copy-Item $bridgeSrc $bridgeDst -Force
    Write-Host "  COPY klor-bridge-windows.py" -ForegroundColor Green
}

# ─── API key setup ────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== API Key Setup ===" -ForegroundColor Cyan
Write-Host "Set your API keys using Python keyring:" -ForegroundColor Yellow
Write-Host ""
Write-Host '  python -c "import keyring; keyring.set_password(''klor-bridge'', ''openrouter_key'', ''sk-or-YOUR-KEY'')"' -ForegroundColor White
Write-Host '  python -c "import keyring; keyring.set_password(''klor-bridge'', ''elevenlabs_key'', ''YOUR-KEY'')"' -ForegroundColor White
Write-Host ""
Write-Host "Or set environment variables:" -ForegroundColor Yellow
Write-Host '  $env:KLOR_OPENROUTER_KEY = "sk-or-..."' -ForegroundColor White
Write-Host '  $env:KLOR_ELEVENLABS_KEY = "..."' -ForegroundColor White

# ─── Running instructions ─────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Running ===" -ForegroundColor Cyan
Write-Host "Start the bridge daemon:" -ForegroundColor Yellow
Write-Host "  python $bridgeDst" -ForegroundColor White
Write-Host ""
Write-Host "With debug logging:" -ForegroundColor Yellow
Write-Host "  python $bridgeDst --verbose" -ForegroundColor White
Write-Host ""
Write-Host "To run at startup, create a scheduled task or shortcut in shell:startup" -ForegroundColor Yellow
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
