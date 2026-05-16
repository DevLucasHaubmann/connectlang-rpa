# Hook: session-end
# Executado ao encerrar a sessão do Claude Code.
# Registra fim da sessão na nota ativa e exibe lembrete de pendências.

$vaultPath = $env:OBSIDIAN_VAULT_PATH

if (-not $vaultPath) {
    Write-Host "[session-end] OBSIDIAN_VAULT_PATH não configurado. Pulando registro."
    exit 0
}

if (-not (Test-Path $vaultPath)) {
    Write-Host "[session-end] Diretório do vault não encontrado: $vaultPath. Pulando registro."
    exit 0
}

# Resolve arquivo de sessão: sempre busca o mais recente em OBSIDIAN_SESSIONS_DIR
$sessionsDir     = if ($env:OBSIDIAN_SESSIONS_DIR) { $env:OBSIDIAN_SESSIONS_DIR } else { "RPA ConnectLang/01 - Sessões" }
$sessionsDirFull = Join-Path $vaultPath $sessionsDir
$sessionFile     = $null

if (Test-Path $sessionsDirFull) {
    $latest = Get-ChildItem $sessionsDirFull -Filter "sessao-*.md" |
              Sort-Object LastWriteTime -Descending |
              Select-Object -First 1
    if ($latest) { $sessionFile = $latest.FullName }
}

if (-not $sessionFile -or -not (Test-Path $sessionFile)) {
    Write-Host "[session-end] Nenhuma nota de sessão encontrada. Pulando registro."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$endMarker = "`n---`n**Fim da sessão:** $timestamp`n"

try {
    $content = [System.IO.File]::ReadAllText($sessionFile, [System.Text.Encoding]::UTF8)

    # Evita duplicar o marcador de fim
    if ($content -notmatch "Fim da sessão:") {
        $content += $endMarker
        [System.IO.File]::WriteAllText($sessionFile, $content, [System.Text.Encoding]::UTF8)
        Write-Host "[session-end] Sessão encerrada registrada em: $sessionFile"
    }
    else {
        Write-Host "[session-end] Fim de sessão já registrado. Nenhuma alteração."
    }
}
catch {
    Write-Host "[session-end] Falha ao registrar fim de sessão."
    exit 0
}

Write-Host "[session-end] Lembrete: edite a seção 'Pendências / Próxima Task' em $sessionFile"

exit 0