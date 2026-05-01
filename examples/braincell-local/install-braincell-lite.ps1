<#
.SYNOPSIS
    Install BrainCell Lite — persistent memory for GitHub Copilot.

.DESCRIPTION
    Copies .braincell/SKILL.md, .braincell/memories.json, and the
    copilot-instructions block into any local Git repository.
    Run this script from the root of the target repo, or pass -TargetPath.

.PARAMETER TargetPath
    Path to the repository root. Defaults to current directory.

.PARAMETER SkipCommit
    Skip the optional git commit at the end.

.PARAMETER Force
    Overwrite existing .braincell files without asking.

.EXAMPLE
    # Install in current repo
    .\install-braincell-lite.ps1

.EXAMPLE
    # Install in a specific repo
    .\install-braincell-lite.ps1 -TargetPath "C:\repos\my-project"

.EXAMPLE
    # Install silently, no commit
    .\install-braincell-lite.ps1 -SkipCommit -Force
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string] $TargetPath  = (Get-Location).Path,
    [switch] $SkipCommit,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'

# ── Helpers ────────────────────────────────────────────────────────────────

function Write-Step  ([string]$Msg) { Write-Host "  + $Msg" -ForegroundColor Cyan }
function Write-Ok    ([string]$Msg) { Write-Host "    $Msg" -ForegroundColor Green }
function Write-Warn  ([string]$Msg) { Write-Host "    ! $Msg" -ForegroundColor Yellow }
function Write-Fail  ([string]$Msg) { Write-Host "    x $Msg" -ForegroundColor Red }
function Write-Title ([string]$Msg) { Write-Host "`n$Msg" -ForegroundColor White }

# ── Validate target ────────────────────────────────────────────────────────

Write-Title "BrainCell Lite — Installer"
Write-Host  "  Target: $TargetPath`n"

if (-not (Test-Path $TargetPath)) {
    Write-Fail "Target path does not exist: $TargetPath"
    exit 1
}

$gitDir = Join-Path $TargetPath ".git"
if (-not (Test-Path $gitDir)) {
    Write-Fail "No .git directory found in $TargetPath"
    Write-Fail "BrainCell Lite must be installed inside a Git repository."
    exit 1
}

# ── Paths ──────────────────────────────────────────────────────────────────

$braincellDir   = Join-Path $TargetPath ".braincell"
$githubDir      = Join-Path $TargetPath ".github"
$memoriesFile   = Join-Path $braincellDir "memories.json"
$skillFile      = Join-Path $braincellDir "SKILL.md"
$instructFile   = Join-Path $githubDir   "copilot-instructions.md"

# ── Create directories ─────────────────────────────────────────────────────

Write-Title "Creating directories"

foreach ($dir in @($braincellDir, $githubDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Ok "Created $dir"
    } else {
        Write-Ok "Exists  $dir"
    }
}

# ── Write memories.json ────────────────────────────────────────────────────

Write-Title "Writing .braincell/memories.json"

if ((Test-Path $memoriesFile) -and -not $Force) {
    Write-Warn "memories.json already exists — skipping (use -Force to overwrite)"
} else {
    $now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $id  = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss") + "-note"

    $memoriesContent = @"
{
  "version": "1.0",
  "updated": "$now",
  "entries": [
    {
      "id": "$id",
      "type": "note",
      "title": "BrainCell Lite initialized",
      "content": "Memory store initialized. Add entries here as the project grows.",
      "tags": ["setup"],
      "created": "$now",
      "updated": "$now"
    }
  ]
}
"@
    Set-Content -Path $memoriesFile -Value $memoriesContent -Encoding UTF8
    Write-Ok "Written memories.json"
}

# ── Write SKILL.md ─────────────────────────────────────────────────────────

Write-Title "Writing .braincell/SKILL.md"

if ((Test-Path $skillFile) -and -not $Force) {
    Write-Warn "SKILL.md already exists — skipping (use -Force to overwrite)"
} else {
    $skillContent = @'
# BrainCell Local — Memory Skill

## Purpose
Persistent memory for AI coding sessions using local JSON files only.
No server, no database, no configuration required — just a JSON file in your repo.

---

## Memory Store

**File:** `.braincell/memories.json` (relative to workspace root)

---

## Schema

```json
{
  "version": "1.0",
  "updated": "2026-01-01T00:00:00Z",
  "entries": [
    {
      "id": "20260101-120000-fact",
      "type": "fact|decision|task|note|error|pattern|preference",
      "title": "Short title, max 80 chars",
      "content": "Full content of the memory",
      "tags": ["tag1", "tag2"],
      "created": "2026-01-01T12:00:00Z",
      "updated": "2026-01-01T12:00:00Z"
    }
  ]
}
```

**Type definitions:**
| Type       | When to use                                                  |
|------------|--------------------------------------------------------------|
| `fact`     | Project facts, versions, key URLs, credentials structure     |
| `decision` | Architecture or approach decisions made during the session   |
| `task`     | Tasks — include status: open/done/blocked                    |
| `note`     | General context, summaries, session notes                    |
| `error`    | Bugs found and fixed — capture the solution pattern          |
| `pattern`  | Reusable code patterns, working commands, solutions          |
| `preference` | User preferences, style rules, constraints                 |

---

## Procedures

### 1. Session Start — Always Load Memory

**At the start of every conversation**, check if `.braincell/memories.json` exists.
If it exists, read it immediately using `read_file` and use its contents as context.

```
read_file(".braincell/memories.json")
```

If the file does not exist, skip silently. Do not create it until something worth saving occurs.

---

### 2. Initialize (first write)

If `.braincell/memories.json` does not exist yet, create it:

```json
{
  "version": "1.0",
  "updated": "NOW_ISO8601",
  "entries": []
}
```

---

### 3. Add a Memory Entry

1. Read current `.braincell/memories.json`
2. Generate id: `YYYYMMDD-HHMMSS-{type}` (use current datetime)
3. Build the new entry object
4. Append to `entries` array
5. Update root `updated` timestamp
6. Write back using `replace_string_in_file`

---

### 4. Search Memories

Use `grep_search` scoped to `.braincell/memories.json` with a relevant keyword.
For full context, use `read_file` on the file directly.

---

### 5. Update an Existing Entry

1. Read `.braincell/memories.json`
2. Find the entry by `id`
3. Update `content` and `updated` timestamp
4. Write back using `replace_string_in_file`

---

### 6. Mark a Task Done

Find the task entry, change `"status: open"` in content to `"status: done"`, update timestamp.

---

## When to Write a Memory

**DO write when:**
- User states a preference, constraint, or rule
- A bug is found and fixed (capture the solution pattern)
- An architectural decision is made
- A working command or solution is discovered
- A task is created or completed
- Important project context is shared

**DO NOT write when:**
- Answering simple/trivial questions
- Information is obvious from the code
- The user has not shared anything new

---

## Announce Memory Operations

When saving a memory, briefly tell the user:
> "Saved to memory: [title]"

When loading memories at session start with entries present:
> "Loaded [N] memories from .braincell/memories.json"

When there is nothing relevant in memory, say nothing.
'@
    Set-Content -Path $skillFile -Value $skillContent -Encoding UTF8
    Write-Ok "Written SKILL.md"
}

# ── Write / append copilot-instructions.md ────────────────────────────────

Write-Title "Writing .github/copilot-instructions.md"

$instructBlock = @'

---
<!-- BEGIN:braincell-lite -->
# BrainCell Lite — Persistent AI Memory

This project uses **BrainCell Lite** for persistent AI memory stored in `.braincell/memories.json`.

## REQUIRED — Every Session Start

Before answering any question or starting any task:

1. Use `read_file` to load `.braincell/SKILL.md` — this contains the full memory skill
2. Check if `.braincell/memories.json` exists and read it for context
3. Apply all procedures from the skill for the remainder of the session

```
read_file(".braincell/SKILL.md")
```

## REQUIRED — During the Session

Follow `.braincell/SKILL.md` for all memory operations:

- **Save** important context, decisions, preferences, and solutions
- **Announce** saves briefly: "Saved to memory: [title]"
- **Search** memory before answering questions about past context

## Memory File Location

`.braincell/memories.json` — committed to the repo, version-controlled with the project.

Do not store secrets or credentials in memory.
<!-- END:braincell-lite -->
'@

if (Test-Path $instructFile) {
    $existing = Get-Content $instructFile -Raw

    if ($existing -match 'BEGIN:braincell-lite') {
        Write-Warn "copilot-instructions.md already contains BrainCell Lite block — skipping"
    } else {
        Add-Content -Path $instructFile -Value $instructBlock -Encoding UTF8
        Write-Ok "Appended BrainCell Lite block to existing copilot-instructions.md"
    }
} else {
    $newContent = "# Copilot Instructions`n" + $instructBlock
    Set-Content -Path $instructFile -Value $newContent -Encoding UTF8
    Write-Ok "Created copilot-instructions.md"
}

# ── Git commit ─────────────────────────────────────────────────────────────

if (-not $SkipCommit) {
    Write-Title "Git commit"

    $answer = Read-Host "  Commit these files now? [Y/n]"
    if ($answer -eq '' -or $answer -match '^[Yy]') {
        Push-Location $TargetPath
        try {
            git add ".braincell/" ".github/copilot-instructions.md" 2>&1 | Out-Null
            git commit -m "chore: add BrainCell Lite persistent memory" 2>&1 | Out-Null
            Write-Ok "Committed: chore: add BrainCell Lite persistent memory"
        } catch {
            Write-Warn "Git commit failed: $_"
        } finally {
            Pop-Location
        }
    } else {
        Write-Warn "Skipped commit. Run manually:"
        Write-Host "    git add .braincell/ .github/copilot-instructions.md"
        Write-Host "    git commit -m `"chore: add BrainCell Lite persistent memory`""
    }
} else {
    Write-Title "Skipping git commit (-SkipCommit)"
    Write-Host "  Run manually when ready:"
    Write-Host "    git add .braincell/ .github/copilot-instructions.md"
    Write-Host "    git commit -m `"chore: add BrainCell Lite persistent memory`""
}

# ── Done ───────────────────────────────────────────────────────────────────

Write-Title "Done"
Write-Host "  BrainCell Lite is installed in: $TargetPath"
Write-Host "  Open a new Copilot Chat conversation to activate memory.`n"
