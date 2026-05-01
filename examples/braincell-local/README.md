# BrainCell Lite

**Persistent memory for GitHub Copilot using local JSON files.**  
No server. No database. No account. One PowerShell command.

---

## What is this?

BrainCell Lite gives GitHub Copilot a long-term memory that survives between sessions.  
Decisions, preferences, working solutions, and tasks are stored in topic-scoped JSON files  
under `.braincell/` and automatically injected into every Copilot Chat session via a VS Code lifecycle hook.

---

## Installation — one command

Run this from the root of any local Git repository:

```powershell
irm https://raw.githubusercontent.com/ITlusions/ITL.BrainCell/main/examples/braincell-local/install-braincell-lite.ps1 | iex
```

Or download and run locally:

```powershell
.\install-braincell-lite.ps1
```

The installer:
- Creates `.braincell/` with an initial notes file and search index
- Writes `.braincell/SKILL.md` — the full memory skill
- Adds the BrainCell block to `.github/copilot-instructions.md` (creates it if missing)
- Installs the SessionStart hook under `.github/hooks/` and `.github/scripts/`
- Offers an optional git commit

**Options:**

| Flag | Description |
|---|---|
| `-TargetPath <path>` | Install into a specific repo (default: current directory) |
| `-SkipCommit` | Skip the git commit prompt |
| `-Force` | Overwrite existing `.braincell` files |

---

## File structure after install

```
your-repo/
├── .braincell/
│   ├── SKILL.md                         ← full memory skill
│   ├── braincell-lite-index.json        ← fast-search index (auto-maintained)
│   └── braincell-lite-notes.json        ← initial memory store (topic: notes)
└── .github/
    ├── copilot-instructions.md          ← activation hook
    ├── hooks/
    │   └── braincell-hooks.json         ← VS Code SessionStart hook config
    └── scripts/
        └── braincell-session-start.ps1  ← injects memory context at session start
```

---

## How it works

1. **Session start**: The VS Code hook runs `braincell-session-start.ps1`, which loads all  
   `braincell-lite-*.json` topic files and injects a context summary into the Copilot Chat session
2. **During session**: Copilot saves important context (decisions, solutions, tasks) to the correct topic file  
   and updates `braincell-lite-index.json` for fast lookup
3. **Next session**: Previous context is automatically available — no prompt needed

---

## Topic-scoped memory files

Each memory type lives in its own file. New topic files are created on demand.

| File | Topic | What goes in it |
|---|---|---|
| `braincell-lite-notes.json` | `notes` | General context, session summaries |
| `braincell-lite-decisions.json` | `decisions` | Architecture and approach decisions |
| `braincell-lite-tasks.json` | `tasks` | Tasks with open/done/blocked status |
| `braincell-lite-errors.json` | `errors` | Bugs found and fixed — solution captured |
| `braincell-lite-patterns.json` | `patterns` | Working commands, reusable solutions |
| `braincell-lite-facts.json` | `facts` | Tech stack, versions, key project facts |
| `braincell-lite-preferences.json` | `preferences` | Style rules, constraints, conventions |

Custom topics are allowed — for example `braincell-lite-auth.json` or `braincell-lite-api.json`.

---

## Example entry

```json
{
  "id": "20260427-143000-decision",
  "type": "decision",
  "title": "Use Alembic for database migrations",
  "content": "Decided to use Alembic over manual SQL scripts. Run: alembic upgrade head.",
  "tags": ["database", "migrations"],
  "created": "2026-04-27T14:30:00Z",
  "updated": "2026-04-27T14:30:00Z"
}
```

---

## Customizing

- **Edit any `braincell-lite-*.json` file** directly to add project context upfront
- **Edit `.braincell/SKILL.md`** to change when/how memories are saved
- **Add new topics** by asking Copilot to save to a custom topic (e.g. `braincell-lite-auth.json`)

---

## Privacy

All memories are stored locally in your repository.  
Nothing is sent to any external service. BrainCell Lite has no network component, no telemetry, and no dependencies.  
Do not commit secrets, passwords, or API tokens to memory.

---

## Part of BrainCell

BrainCell Lite is the zero-dependency variant of [ITL BrainCell](https://github.com/ITlusions/ITL.BrainCell) —  
a full persistent memory platform for AI agents with PostgreSQL, Weaviate, and REST/MCP APIs.

For teams and production use, see the full BrainCell platform.

---

## License

MIT
