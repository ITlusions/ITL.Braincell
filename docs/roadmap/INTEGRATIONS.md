# External Integrations

Planned integrations that connect BrainCell memory to external systems.

---

## 1. GitHub

**Status**: `planned`
**Priority**: medium

### Use cases
- Auto-link `files_discussed` records to the Git commit or PR that last touched that file
- When a `tasks` record is created → optionally open a GitHub Issue
- When a decision references a file → link to the file in GitHub

### Approach
Use the GitHub REST API (`/repos/{owner}/{repo}/commits?path={file_path}`) to resolve the last commit for a file. Store the commit SHA + PR URL on the `FileDiscussed` record.

### New field on `FileDiscussed`
```python
last_commit_sha: Optional[str]
last_pr_url: Optional[str]
```

### Configuration
```env
GITHUB_TOKEN=ghp_...
GITHUB_REPO=ITlusions/ITL.BrainCell
```

---

## 2. Jira / Azure DevOps

**Status**: `planned`
**Priority**: medium

### Use cases
- `tasks` with `priority='high'` → auto-create a Jira ticket or Azure DevOps work item
- `research_questions` with `status='investigating'` → link to an existing ticket
- Two-way sync: when ticket closes → update `tasks` status to `done`

### Approach
Pluggable backend: a `tasks/integrations/` submodule with `jira.py` and `azuredevops.py`. Called fire-and-forget from `task_save`.

### Configuration
```env
TASK_INTEGRATION=jira  # or azuredevops
JIRA_URL=https://itlusions.atlassian.net
JIRA_TOKEN=...
JIRA_PROJECT=BRAIN
```

---

## 3. Slack / Microsoft Teams

**Status**: `planned`
**Priority**: low

### Use cases
- Notify a channel when a `high` priority research question is auto-detected
- Post a design decision summary to a decisions channel
- Send the weekly `memory_digest` to a #braincell-weekly channel every Monday

### Approach
Webhook-based. Add `SLACK_WEBHOOK_URL` or `TEAMS_WEBHOOK_URL` to `.env`. Triggered from relevant cell `_save` functions when priority/status criteria are met.

### Configuration
```env
NOTIFICATION_BACKEND=slack  # or teams
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
NOTIFY_ON_HIGH_PRIORITY=true
NOTIFY_ON_NEW_DECISION=true
```

---

## 4. Keycloak — Per-user memory

**Status**: `planned`
**Priority**: high

### Problem
All memory is currently shared. In a multi-user or multi-team setup, every agent sees everyone's data.

### Solution
Add `owner_id` (Keycloak user UUID) and `team_id` to all cell models. Filter all queries by the JWT `sub` claim.

### Changes required
1. All models: add `owner_id: Optional[str]` and `team_id: Optional[str]`
2. All `_save` tools: extract `owner_id` from request context (passed via MCP call metadata)
3. All `_list` / `_search` tools: filter by `owner_id` or `team_id`
4. Weaviate: add `owner_id` as a filterable property on all collections

### ITLAuth integration
BrainCell already sits behind ITLAuth (Keycloak). The JWT is available at the MCP layer. Pass `sub` claim down to cell functions via a context variable.

### Configuration
```env
KEYCLOAK_ISSUER=https://auth.itlusions.com/realms/itl
KEYCLOAK_AUDIENCE=braincell
MEMORY_SCOPE=user  # or team or global
```

---

## 5. BrainCell as a shared team memory

**Status**: `planned` (depends on Keycloak integration)
**Priority**: low

### Vision
Multiple developers in the same team share a BrainCell instance. Each person's interactions feed into shared `decisions`, `architecture_notes`, `files_discussed`, and `research_questions` pools — but personal `snippets` and `notes` remain private.

### Access model
| Cell | Scope |
|------|-------|
| `decisions` | team |
| `architecture_notes` | team |
| `files_discussed` | team |
| `research_questions` | team |
| `interactions` | user |
| `snippets` | user |
| `notes` | user |
| `tasks` | configurable |
