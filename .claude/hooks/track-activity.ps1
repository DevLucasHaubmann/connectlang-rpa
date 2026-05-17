# Hook: track-activity
# Recebe evento via STDIN (JSON) e registra atividade relevante no Obsidian.
# Caminhos sensíveis são ignorados. Falhas não críticas resultam em exit 0.

$SENSITIVE_PATTERNS = @('.env', 'browser-profile', 'screenshots', '\blogs?\b', 'tokens?', 'cookies?')

function Test-SensitivePath {
    param([string]$path)
    foreach ($pattern in $SENSITIVE_PATTERNS) {
        if ($path -match $pattern) { return $true }
    }
    return $false
}

# Leitura defensiva do STDIN
$rawInput = $null
try {
    $rawInput = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($rawInput)) { $rawInput = $null }
}
catch { $rawInput = $null }

$event = $null
if ($rawInput) {
    try { $event = $rawInput | ConvertFrom-Json -ErrorAction Stop }
    catch { $event = $null }
}

# Resolve arquivo de sessão: sempre busca o mais recente em OBSIDIAN_SESSIONS_DIR
$vaultPath = $env:OBSIDIAN_VAULT_PATH
if (-not $vaultPath -or -not (Test-Path $vaultPath)) {
    exit 0
}

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
    exit 0
}

# Extrai campos relevantes do evento
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$eventType = if ($event -and $event.type)        { $event.type }        else { "unknown" }
$tool       = if ($event -and $event.tool_name)  { $event.tool_name }   else { $null }
$filePath   = if ($event -and $event.file_path)  { $event.file_path }   else { $null }
$command    = if ($event -and $event.command)    { $event.command }     else { $null }

# Filtra caminhos sensíveis
if ($filePath -and (Test-SensitivePath $filePath)) { $filePath = "[omitido]" }
if ($command  -and (Test-SensitivePath $command))  { $command  = "[omitido]" }

# Monta linha de log
$parts = @("- **[$timestamp]** tipo=``$eventType``")
if ($tool)     { $parts += "ferramenta=``$tool``" }
if ($filePath) { $parts += "arquivo=``$filePath``" }
if ($command)  { $parts += "comando=``$command``" }

$logLine = ($parts -join " | ") + "`n"

try {
    $content = [System.IO.File]::ReadAllText($sessionFile, [System.Text.Encoding]::UTF8)
    $marker  = "<!-- Preenchido automaticamente por track-activity.ps1 -->"
    if ($content -match [regex]::Escape($marker)) {
        $content = $content -replace [regex]::Escape($marker), "$marker`n$logLine"
    }
    else {
        $content += $logLine
    }
    [System.IO.File]::WriteAllText($sessionFile, $content, [System.Text.Encoding]::UTF8)
}
catch {
    # Falha silenciosa — não interrompe o Claude Code
}

exit 0