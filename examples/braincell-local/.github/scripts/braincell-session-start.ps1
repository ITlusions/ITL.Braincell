<#
.SYNOPSIS
    BrainCell Lite — SessionStart hook.
    Loads all braincell-lite-*.json memory files and injects a context
    summary as a system message into the Copilot chat session.

.NOTES
    Hook contract:
    - Read stdin fully (required, content unused here)
    - Write exactly ONE line to stdout: JSON { "continue": true, "systemMessage": "..." }
    - Exit 0 on success
    - $ErrorActionPreference = 'SilentlyContinue' — never crash the session
#>

$ErrorActionPreference = 'SilentlyContinue'

# ── Hook contract: consume stdin ──────────────────────────────────────────
$null = [Console]::In.ReadToEnd()

# ── Resolve .braincell search roots ──────────────────────────────────────
# Priority: repo root → workspace folder → user profile
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot    = [IO.Path]::GetFullPath((Join-Path $scriptDir '..\..'))
$userProfile = Join-Path $env:USERPROFILE '.braincell'

$searchRoots = @(
    (Join-Path $repoRoot '.braincell'),
    $userProfile
)

# ── Find .braincell directory ─────────────────────────────────────────────
$braincellDir = $null
foreach ($root in $searchRoots) {
    if (Test-Path $root) { $braincellDir = $root; break }
}

# ── If no .braincell found, exit silently ─────────────────────────────────
if (-not $braincellDir) {
    Write-Output '{"continue":true,"systemMessage":""}'
    exit 0
}

# ── Load index first (fast path) ─────────────────────────────────────────
$indexFile   = Join-Path $braincellDir 'braincell-lite-index.json'
$indexData   = $null
$indexSummary = @()

if (Test-Path $indexFile) {
    try {
        $indexData = Get-Content $indexFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $entryCount = ($indexData.entries | Measure-Object).Count
        if ($entryCount -gt 0) {
            $indexSummary += "Index: $entryCount entries across all topics"
            # Surface open tasks from index
            $openTasks = $indexData.entries | Where-Object { $_.type -eq 'task' }
            if ($openTasks) {
                $taskTitles = ($openTasks | Select-Object -First 5 | ForEach-Object { "  - $($_.title)" }) -join "`n"
                $indexSummary += "Tasks in memory:`n$taskTitles"
            }
        }
    } catch { }
}

# ── Load all braincell-lite-*.json topic files ────────────────────────────
$topicFiles  = Get-ChildItem -Path $braincellDir -Filter 'braincell-lite-*.json' -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -ne 'braincell-lite-index.json' }

$loadedFiles  = @()
$contextParts = @()

foreach ($file in $topicFiles) {
    try {
        $data = Get-Content $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $entries = $data.entries
        if (-not $entries) { continue }

        $count = ($entries | Measure-Object).Count
        $topic = if ($data.topic) { $data.topic } else { $file.BaseName -replace 'braincell-lite-', '' }
        $loadedFiles += "$($file.Name) ($count entries)"

        # Build compact context per topic
        $lines = @("[$($topic.ToUpper())]")
        foreach ($entry in $entries | Select-Object -First 10) {
            $lines += "  [$($entry.type)] $($entry.title)"
            if ($entry.content -and $entry.content.Length -gt 0) {
                $snippet = $entry.content -replace '\r?\n', ' '
                if ($snippet.Length -gt 120) { $snippet = $snippet.Substring(0, 120) + '...' }
                $lines += "    $snippet"
            }
        }
        if ($count -gt 10) { $lines += "  ... and $($count - 10) more entries" }

        $contextParts += $lines -join "`n"
    } catch { }
}

# ── Build system message ──────────────────────────────────────────────────
if ($loadedFiles.Count -eq 0 -and $indexSummary.Count -eq 0) {
    Write-Output '{"continue":true,"systemMessage":""}'
    exit 0
}

$header = "## BrainCell Lite — Memory loaded"
$header += "`nFiles: $($loadedFiles -join ', ')"
if ($indexSummary) { $header += "`n$($indexSummary -join "`n")" }

$body = @(
    $header,
    "",
    "Use this memory as context for the current session.",
    "Follow .braincell/SKILL.md for all memory operations.",
    "When adding entries, always update braincell-lite-index.json.",
    "",
    "--- MEMORY CONTENTS ---",
    ($contextParts -join "`n`n")
) -join "`n"

# Escape for JSON string
$escaped = $body `
    -replace '\\', '\\' `
    -replace '"',  '\"' `
    -replace "`r`n", '\n' `
    -replace "`n",   '\n' `
    -replace "`t",   '\t'

Write-Output "{`"continue`":true,`"systemMessage`":`"$escaped`"}"
exit 0
