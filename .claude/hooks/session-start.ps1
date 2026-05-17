# Hook: session-start
# Executado no início de cada sessão do Claude Code.
# Registra início de sessão e garante estrutura base no Obsidian.

$vaultPath = $env:OBSIDIAN_VAULT_PATH

if (-not $vaultPath) {
    Write-Host "[session-start] OBSIDIAN_VAULT_PATH não configurado. Pulando registro."
    exit 0
}

if (-not (Test-Path $vaultPath)) {
    Write-Host "[session-start] Diretório do vault não encontrado: $vaultPath. Pulando registro."
    exit 0
}

$projectNote  = if ($env:OBSIDIAN_PROJECT_NOTE)  { $env:OBSIDIAN_PROJECT_NOTE }  else { "RPA ConnectLang/00 - Roadmap.md" }
$sessionsDir  = if ($env:OBSIDIAN_SESSIONS_DIR)  { $env:OBSIDIAN_SESSIONS_DIR }  else { "RPA ConnectLang/01 - Sessões" }

# Deriva a raiz do projeto a partir do pai de OBSIDIAN_PROJECT_NOTE
$projectNoteParent = Split-Path $projectNote -Parent
$rpaRoot = if ($projectNoteParent) {
    Join-Path $vaultPath $projectNoteParent
} else {
    $vaultPath
}

$sessionsDirFull = Join-Path $vaultPath $sessionsDir
$projectNoteFull = Join-Path $vaultPath $projectNote

# Estrutura base
$dirs = @(
    $rpaRoot,
    $sessionsDirFull
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        try { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        catch { Write-Host "[session-start] Falha ao criar diretório: $dir"; exit 0 }
    }
}

# Notas de referência (criadas apenas se ausentes)
$referenceNotes = @{
    (Join-Path $rpaRoot "02 - Decisões Técnicas.md") = "# Decisões Técnicas`n`n| Data | Decisão | Motivo |`n|------|---------|--------|`n"
    (Join-Path $rpaRoot "03 - Bugs e Pendências.md") = "# Bugs e Pendências`n`n| Data | Item | Status |`n|------|------|--------|`n"
    (Join-Path $rpaRoot "04 - Comandos Úteis.md")    = "# Comandos Úteis`n`n| Comando | Propósito |`n|---------|-----------|`n"
}
foreach ($entry in $referenceNotes.GetEnumerator()) {
    if (-not (Test-Path $entry.Key)) {
        try { [System.IO.File]::WriteAllText($entry.Key, $entry.Value, [System.Text.Encoding]::UTF8) }
        catch { Write-Host "[session-start] Falha ao criar nota: $($entry.Key)" }
    }
}

# Nota principal do projeto (cria se ausente)
if (-not (Test-Path $projectNoteFull)) {
    $projectContent = @"
# ConnectLang RPA Bot

Projeto de automação RPA para a plataforma ConnectLang.

## Stack
- Python 3.12 + Playwright
- uv, pydantic-settings, structlog, tenacity, pytest

## Links
- Repositório: connectlang-rpa
- Sessões: [[01 - Sessões]]

## Roadmap resumido
| Task | Título | Status |
|------|--------|--------|
| 0.1 | Estrutura base | ✅ |
| 0.2 | Agentes RPA | ✅ |
| 0.3 | CLAUDE.md | ✅ |
| 0.4 | Rules | ✅ |
| 0.5 | Subagentes | ✅ |
| 0.6 | Obsidian hooks | ✅ |
| 0.7 | Claude settings | ⏳ |
"@
    try { [System.IO.File]::WriteAllText($projectNoteFull, $projectContent, [System.Text.Encoding]::UTF8) }
    catch { Write-Host "[session-start] Falha ao criar nota principal." }
}

# Nota de sessão
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dateLabel = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$sessionFile = Join-Path $sessionsDirFull "sessao-$timestamp.md"

$sessionContent = @"
# Sessão — $dateLabel

**Projeto:** ConnectLang RPA Bot
**Início:** $dateLabel

## Atividades

<!-- Preenchido automaticamente por track-activity.ps1 -->

## Pendências / Próxima Task

<!-- Edite manualmente ao encerrar a sessão -->

"@

try {
    [System.IO.File]::WriteAllText($sessionFile, $sessionContent, [System.Text.Encoding]::UTF8)
    Write-Host "[session-start] Sessão registrada: $sessionFile"
}
catch {
    Write-Host "[session-start] Falha ao criar nota de sessão."
}

exit 0