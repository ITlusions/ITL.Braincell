# BrainCell Local — Persistent AI Memory

This project uses **BrainCell Local** for persistent AI memory stored in `.braincell/memories.json`.

---

## REQUIRED — Every Session Start

Before answering any question or starting any task:

1. Search for `.braincell/SKILL.md` in this order and load the first match:
   - `{workspace_root}/.braincell/SKILL.md`
   - `{workspace_folder}/.braincell/SKILL.md`
   - `~/.braincell/SKILL.md`
2. Scan for all `braincell-lite-*.json` files in the same locations and read every file found for context
3. Apply all procedures from the skill for the remainder of the session

```
read_file("{workspace_root}/.braincell/SKILL.md")
```

---

## REQUIRED — During the Session

Follow `.braincell/SKILL.md` for all memory operations:

- **Save** important context, decisions, preferences, and solutions
- **Announce** saves briefly: "Saved to memory: [title]"
- **Search** memory before answering questions about past context

---

## Memory File Location

`.braincell/memories.json` — committed to the repo, version-controlled with the project.

Do not store secrets or credentials in memory.
