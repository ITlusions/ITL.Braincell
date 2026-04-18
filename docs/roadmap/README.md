# BrainCell — Roadmap

This folder describes planned improvements to BrainCell: new memory cells, smarter auto-detection, cross-cell intelligence, and external integrations.

## Status legend

| Status | Meaning |
|--------|---------|
| `planned` | Agreed on, not yet started |
| `in-progress` | Currently being implemented |
| `done` | Merged to `main` |

---

## Overview

| Area | Document | Summary |
|------|----------|---------|
| New cells | [PLANNED_CELLS.md](./PLANNED_CELLS.md) | `tasks`, `references`, `errors`, `persons`, `versions` |
| Smarter auto-detection | [INTELLIGENCE.md](./INTELLIGENCE.md) | Cross-cell linking, duplicate detection, priority scoring, session context injection, weekly digest |
| External integrations | [INTEGRATIONS.md](./INTEGRATIONS.md) | GitHub, Jira/Azure DevOps, Slack/Teams, Keycloak per-user memory |
| Advanced features | [ADVANCED.md](./ADVANCED.md) | Contradictie-detectie, kennisgraaf, proactieve context push, multi-agent geheugen, fine-tuning export |

---

## Immediate backlog (highest priority)

1. **Add `ResearchQuestion` to `CELL_MAP`** in `src/cells/jobs/cell.py` — retention/archive job does not yet cover this cell.
2. **Duplicate detection** on `decisions` and `research_questions` before inserting — use Weaviate distance < 0.15.
3. **`tasks` cell** — action items are not captured anywhere yet.
4. **Session context injection** — inject open questions + recent decisions at session start.

---

## Completed auto-detection (as of commit `333baae`)

These detectors run automatically inside `interactions_save`:

| Detector | Trigger | Target cell |
|----------|---------|-------------|
| Research questions | `role='user'` + question heuristic | `research_questions` (status=`pending`) |
| Code snippets | `role='assistant'` + fenced code block | `snippets` |
| Files discussed | any role + file path pattern | `files_discussed` (upsert) |
| Design decisions | `role='assistant'` + NL/EN decision pattern | `decisions` (status=`proposed`) |
| Auto-answer | `role='assistant'` + Weaviate distance < 0.25 on pending question | `research_questions` (status=`answered`) |
