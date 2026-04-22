# BrainCell MCP — Agent Integration

## Claude Desktop

### Streamable HTTP (recommended, server running in Docker)

Edit `~/.config/claude/claude_desktop_config.json` (Linux/macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "braincell": {
      "type": "http",
      "url": "http://localhost:9506/mcp"
    }
  }
}
```

Restart Claude Desktop after saving.

### stdio (local process, no Docker required)

```json
{
  "mcpServers": {
    "braincell": {
      "command": "python",
      "args": ["-m", "src.mcp.server_stdio"],
      "cwd": "/path/to/ITL.BrainCell",
      "env": {
        "DATABASE_URL": "postgresql://braincell:braincell@localhost:9500/braincell"
      }
    }
  }
}
```

---

## GitHub Copilot (VS Code)

Add to `.vscode/mcp.json` in the workspace root (or to user settings):

```json
{
  "servers": {
    "braincell": {
      "type": "http",
      "url": "http://localhost:9506/mcp"
    }
  }
}
```

Then in a Copilot chat agent thread, BrainCell tools appear automatically.

---

## Python — `fastmcp` client

```python
from fastmcp import Client

async with Client("http://localhost:9506/mcp") as client:
    # List all available tools
    tools = await client.list_tools()

    # Save a task
    result = await client.call_tool("tasks_save", {
        "title": "Implement refresh token rotation",
        "priority": "high",
        "project": "ITLAuth",
        "status": "open"
    })

    # Search across all memory
    hits = await client.call_tool("search_memory", {
        "query": "token rotation",
        "memory_type": "decisions"
    })
```

---

## Python — raw HTTP (no MCP SDK)

```python
import httpx

BASE = "http://localhost:9506/mcp"

def call_tool(name: str, arguments: dict) -> dict:
    resp = httpx.post(
        BASE,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        },
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()

# Example: save an IOC
call_tool("ioc_save", {"value": "198.51.100.42", "severity": "high", "source": "honeypot"})
```

---

## TypeScript / Node.js

```ts
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:9506/mcp")
);
const client = new Client({ name: "my-agent", version: "1.0.0" }, { capabilities: {} });
await client.connect(transport);

const result = await client.callTool({
  name: "notes_save",
  arguments: { title: "Deploy checklist", content: "1. Run migrations\n2. Restart pods" }
});
```

---

## Docker Compose — Agent sidecar pattern

```yaml
services:
  my-agent:
    image: my-agent:latest
    environment:
      BRAINCELL_MCP_URL: http://braincell-mcp:9506/mcp
    depends_on:
      - braincell-mcp
    networks:
      - braincell_net

networks:
  braincell_net:
    external: true
    name: itl_braincell_network
```

---

## System prompt snippet for AI agents

Paste into your agent's system prompt to teach it how to use BrainCell:

```
You have access to a persistent memory system called BrainCell via MCP tools.

Rules:
- Before creating tasks or decisions, call <tool>tasks_search</tool> or <tool>decisions_search</tool> to avoid duplicates.
- After every meaningful exchange, save interactions with <tool>interactions_save</tool>. This triggers auto-detection of code snippets, IOCs, file paths, and design decisions.
- When you spot a design decision, ALSO call <tool>decisions_save</tool> explicitly.
- When you encounter an IP address, hash, CVE, or domain in a security context, call <tool>ioc_save</tool>.
- At the start of a session, call <tool>get_relevant_context</tool> with the current task description to prime yourself with prior context.
```

---

## Troubleshooting

### Tools not showing up in Claude Desktop

1. Confirm the MCP server is running: `curl http://localhost:9506/mcp`
2. Check the server logs: `docker compose logs braincell-mcp`
3. Verify the URL in the config file is correct and reachable from the host.

### `connection refused`

The `braincell-mcp` container may not have started. Run:

```bash
docker compose up -d braincell-mcp
docker compose ps braincell-mcp
```

### `tool not found`

Cell registration failed at startup. Check the MCP server logs for import errors:

```bash
docker compose logs braincell-mcp | grep -i error
```
