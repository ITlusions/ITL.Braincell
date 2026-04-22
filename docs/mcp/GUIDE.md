# BrainCell — MCP Server Guide

## Overview

BrainCell exposes its memory capabilities through the **Model Context Protocol (MCP)**. AI agents (Claude, GitHub Copilot, custom agents) can call BrainCell tools over MCP to persist and retrieve knowledge across sessions.

---

## Choosing a Server Variant

BrainCell ships four MCP server implementations. Pick the right one for your use case:

| File               | Port | Transport             | When to use                                |
|--------------------|------|-----------------------|--------------------------------------------|
| `server_http.py`   | 9506 | Streamable HTTP (FastMCP) | **Default.** Remote agents, Docker, production. Stateless — horizontally scalable. |
| `server_stdio.py`  | —    | stdio (JSON-RPC)      | Claude Desktop, local MCP tooling. Launched as a subprocess. |
| `server_lean.py`   | 9506 | HTTP (legacy FastAPI) | Minimal HTTP fallback for clients that can't use FastMCP. |
| `server.py`        | —    | HTTP (legacy FastAPI) | Original prototype. Covers only 6 original entity types. Do not use in new integrations. |

**Recommendation:** Use `server_http.py` for all new integrations. It auto-discovers every installed cell and exposes all their tools without needing manual changes.

---

## Running the MCP Server

### Docker (recommended)

```bash
docker compose up -d braincell-mcp
```

The MCP server starts on port **9506**.

### Direct (dev)

```bash
# Streamable HTTP
uvicorn src.mcp.server_http:app --host 0.0.0.0 --port 9506

# stdio (Claude Desktop)
python -m src.mcp.server_stdio
```

---

## Tool Auto-Discovery

`server_http.py` uses BrainCell's cell plugin system. At startup it calls:

```python
for cell in discover_cells():
    cell.register_mcp_tools(mcp)
```

Every installed cell registers its own tools. Adding a new cell automatically exposes its MCP tools — no changes to the server file are needed.

---

## Available Tools

### Cross-cell tools (built into `server_http.py`)

| Tool                   | Purpose                                                     |
|------------------------|-------------------------------------------------------------|
| `search_memory`        | Keyword search across decisions, snippets, architecture notes |
| `get_relevant_context` | Semantic search + recent active decisions for a given query |

### Conversations cell

| Tool                   | Signature                                         |
|------------------------|---------------------------------------------------|
| `conversations_search` | `(query: str, limit: int = 10)`                  |
| `conversations_save`   | `(session_name: str, summary?: str, ...)`         |
| `conversations_list`   | `(limit: int = 50)`                               |

### Sessions cell

| Tool              | Signature                                               |
|-------------------|---------------------------------------------------------|
| `sessions_search` | `(query: str, limit: int = 10)`                        |
| `sessions_save`   | `(session_name: str, status?: str, summary?: str, ...)` |
| `sessions_list`   | `(limit: int = 50)`                                    |

### Interactions cell

Interactions are the primary ingestion point. Saving an interaction triggers **auto-detection** of sub-entities.

| Tool                   | Signature                                                   |
|------------------------|-------------------------------------------------------------|
| `interactions_search`  | `(query: str, limit: int = 10)`                            |
| `interactions_save`    | `(content: str, role: str, conversation_id?: str, session_id?: str, ...)` |
| `interactions_list`    | `(limit: int = 50)`                                        |

**Auto-detection on save:**
- User question → `research_questions`
- Fenced code block in assistant message → `snippets`
- File path pattern → `files_discussed`
- Decision language in assistant message → `decisions`
- IP / hash / CVE / domain → `iocs`

### Design Decisions cell

| Tool               | Signature                                                         |
|--------------------|-------------------------------------------------------------------|
| `decisions_search` | `(query: str, limit: int = 10)`                                  |
| `decisions_save`   | `(decision: str, rationale?: str, impact?: str, status?: str, ...)` |
| `decisions_list`   | `(limit: int = 50)`                                              |

### Architecture Notes cell

| Tool                        | Signature                                         |
|-----------------------------|---------------------------------------------------|
| `architecture_notes_search` | `(query: str, limit: int = 10)`                  |
| `architecture_notes_save`   | `(component: str, description: str, tags?: list, ...)` |
| `architecture_notes_list`   | `(limit: int = 50)`                              |

### Code Snippets cell

| Tool              | Signature                                                         |
|-------------------|-------------------------------------------------------------------|
| `snippets_search` | `(query: str, limit: int = 10)`                                  |
| `snippets_save`   | `(title: str, code_content: str, language?: str, description?: str, ...)` |
| `snippets_list`   | `(limit: int = 50)`                                              |

### Files Discussed cell

| Tool                      | Signature                                       |
|---------------------------|-------------------------------------------------|
| `files_discussed_search`  | `(query: str, limit: int = 10)`                |
| `files_discussed_save`    | `(file_path: str, language?: str, description?: str, ...)` |
| `files_discussed_list`    | `(limit: int = 50)`                            |

### Notes cell

| Tool           | Signature                                                |
|----------------|----------------------------------------------------------|
| `notes_search` | `(query: str, limit: int = 10)`                         |
| `notes_save`   | `(title: str, content: str, tags?: list, source?: str)` |
| `notes_list`   | `(limit: int = 50)`                                     |

### Research Questions cell

| Tool              | Signature                                                              |
|-------------------|------------------------------------------------------------------------|
| `question_save`   | `(question: str, status?: str, priority?: str, context?: str, ...)`   |
| `question_search` | `(query: str, status?: str, limit: int = 10)`                         |
| `question_list`   | `(status?: str, limit: int = 50)`                                     |

### Tasks cell

| Tool           | Signature                                                                             |
|----------------|---------------------------------------------------------------------------------------|
| `tasks_search` | `(query: str, limit: int = 20)`                                                      |
| `tasks_save`   | `(title: str, description?: str, status?: str, priority?: str, project?: str, ...)` |
| `tasks_list`   | `(status?: str, project?: str, priority?: str, limit: int = 50)`                    |

### Security Incidents cell

| Tool               | Signature                                                          |
|--------------------|--------------------------------------------------------------------|
| `incidents_search` | `(query: str, limit: int = 10)`                                   |
| `incidents_save`   | `(title: str, severity?: str, status?: str, description?: str, ...)` |

### IOCs cell

| Tool         | Signature                                                        |
|--------------|------------------------------------------------------------------|
| `ioc_search` | `(query: str, ioc_type?: str, limit: int = 20)`                |
| `ioc_save`   | `(value: str, type?: str, confidence?: float, severity?: str, ...)` — type is auto-detected if omitted |

### Threats cell (Threat Actors)

| Tool              | Signature                                                         |
|-------------------|-------------------------------------------------------------------|
| `threats_search`  | `(query: str, limit: int = 10)`                                  |
| `threats_save`    | `(name: str, classification?: str, ttps?: list, ...)` |

### Intel Reports cell

| Tool                   | Signature                                                 |
|------------------------|-----------------------------------------------------------|
| `intel_reports_search` | `(query: str, limit: int = 10)`                          |
| `intel_reports_save`   | `(title: str, summary?: str, content?: str, tlp_level?: str, ...)` |

### Vuln Patches cell

| Tool                 | Signature                                                            |
|----------------------|----------------------------------------------------------------------|
| `vuln_patches_search`| `(query: str, language?: str, limit: int = 10)`                    |
| `vuln_patches_save`  | `(title: str, vulnerable_code: str, patched_code: str, language?: str, severity?: str, ...)` |

### Runbooks cell

| Tool               | Signature                                                              |
|--------------------|------------------------------------------------------------------------|
| `runbooks_search`  | `(query: str, category?: str, limit: int = 10)`                       |
| `runbooks_save`    | `(title: str, steps: list, category?: str, trigger?: str, ...)`       |
| `runbooks_get`     | `(runbook_id: str)`                                                   |

### Dependencies cell

| Tool                    | Signature                                                       |
|-------------------------|-----------------------------------------------------------------|
| `dependencies_search`   | `(query: str, ecosystem?: str, status?: str, limit: int = 10)` |
| `dependencies_save`     | `(name: str, version: str, ecosystem?: str, status?: str, ...)` |

### API Contracts cell

| Tool                       | Signature                                             |
|----------------------------|-------------------------------------------------------|
| `api_contracts_search`     | `(query: str, limit: int = 10)`                      |
| `api_contracts_save`       | `(title: str, service_name: str, version: str, ...)`  |
| `api_contracts_list_services` | `(limit: int = 50)`                              |

---

## stdio Server (Claude Desktop)

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "braincell": {
      "command": "python",
      "args": ["-m", "src.mcp.server_stdio"],
      "cwd": "/path/to/ITL.BrainCell"
    }
  }
}
```

---

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:9506/mcp
```

---

## Integration examples

See [INTEGRATION.md](INTEGRATION.md) for Python, Claude Desktop, and GitHub Copilot agent integration examples.
