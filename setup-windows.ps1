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

pip install hidapi openai pyyaml keyring pyautogui pyperclip

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

$configFiles = @("config.yml", "actions.yml", "prompts.yml", "lexicon.yml", "corrections.yml", "snippets.yml")

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

# Copy active code
$bridgeSrc = Join-Path $bridgeDir "klor-bridge-windows.py"
$bridgeDst = Join-Path $configDir "klor-bridge-windows.py"
$adapterSrc = Join-Path $bridgeDir "openwhispr_elevenlabs_shim.py"
$adapterDst = Join-Path $configDir "openwhispr_elevenlabs_shim.py"

if (Test-Path $bridgeSrc) {
    Copy-Item $bridgeSrc $bridgeDst -Force
    Write-Host "  COPY klor-bridge-windows.py" -ForegroundColor Green
}
if (Test-Path $adapterSrc) {
    Copy-Item $adapterSrc $adapterDst -Force
    Write-Host "  COPY openwhispr_elevenlabs_shim.py" -ForegroundColor Green
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

# ─── Running instructions ──────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Running ===" -ForegroundColor Cyan
Write-Host "1. Start OpenWhispr and configure:" -ForegroundColor Yellow
Write-Host "   Dictation hotkey       = Control+Shift+F8 (Toggle)" -ForegroundColor White
Write-Host "   Voice Assistant hotkey = Control+Shift+F9" -ForegroundColor White
Write-Host "   Share screen context   = enabled" -ForegroundColor White
Write-Host "   Speech to Text         = Self-Hosted, http://127.0.0.1:8765, scribe_v2" -ForegroundColor White
Write-Host ""
Write-Host "2. Start the ElevenLabs adapter:" -ForegroundColor Yellow
Write-Host "   python $adapterDst" -ForegroundColor White
Write-Host ""
Write-Host "3. Start the non-voice KLOR bridge:" -ForegroundColor Yellow
Write-Host "   python $bridgeDst" -ForegroundColor White
Write-Host ""
Write-Host "Keyboard voice mappings:" -ForegroundColor Yellow
Write-Host "   RALT x2 -> T = normal OpenWhispr dictation" -ForegroundColor White
Write-Host "   RALT x2 -> C = Voice Assistant + native screen context" -ForegroundColor White
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
