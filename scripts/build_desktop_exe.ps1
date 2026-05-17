# Build script for ConnectLang RPA Bot Desktop App (.exe)
# Usage: .\scripts\build_desktop_exe.ps1
# Output: dist\ConnectLangRpaBot\ConnectLangRpaBot.exe
#
# Requirements:
#   - uv installed and in PATH
#   - pyinstaller in dev dependencies (uv sync --dev)
#   - Run from the project root

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==> ConnectLang RPA Bot — Windows Desktop Build"
Write-Host "    Project root: $ProjectRoot"

Set-Location $ProjectRoot

Write-Host ""
Write-Host "==> [1/3] Running quality gates..."
uv run ruff check .
if ($LASTEXITCODE -ne 0) { Write-Error "ruff failed. Aborting build."; exit 1 }

uv run mypy src
if ($LASTEXITCODE -ne 0) { Write-Error "mypy failed. Aborting build."; exit 1 }

uv run pytest
if ($LASTEXITCODE -ne 0) { Write-Error "pytest failed. Aborting build."; exit 1 }

Write-Host ""
Write-Host "==> [2/3] Building executable with PyInstaller..."
uv run pyinstaller connectlang_desktop.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed."; exit 1 }

Write-Host ""
Write-Host "==> [3/3] Build complete."
Write-Host "    Executable: dist\ConnectLangRpaBot\ConnectLangRpaBot.exe"
Write-Host ""
Write-Host "IMPORTANT — Runtime requirements for the .exe:"
Write-Host "  1. 'uv' must be installed and available in PATH."
Write-Host "  2. The connectlang-rpa project must be installed in the uv environment:"
Write-Host "       uv sync"
Write-Host "  3. Chromium must be installed via Playwright:"
Write-Host "       uv run playwright install chromium"
Write-Host "  4. .env must exist at the project root (3 levels above the .exe)."
Write-Host "  5. The .exe expects to live at dist\ConnectLangRpaBot\ inside the project."
Write-Host "     Do NOT move it outside the project tree — path resolution depends on this."