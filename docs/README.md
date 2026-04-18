# ITL.BrainCell Documentation

## API

| File | Description |
|------|-------------|
| [api/ARCHITECTURE.md](./api/ARCHITECTURE.md) | System architecture — services, ports, modules, data flow, Weaviate schema |
| [api/ENDPOINTS.md](./api/ENDPOINTS.md) | Full REST API reference with request/response examples |

## Deployment

| File | Description |
|------|-------------|
| [deployment/DOCKER.md](./deployment/DOCKER.md) | Local development with `docker compose` — ports, env vars, troubleshooting |
| [deployment/KIND.md](./deployment/KIND.md) | Helm chart testing with a local Kind cluster |
| [deployment/KUBERNETES.md](./deployment/KUBERNETES.md) | Production deployment — Helm install, secrets, scaling, rollback |

## MCP (Model Context Protocol)

| File | Description |
|------|-------------|
| [mcp/GUIDE.md](./mcp/GUIDE.md) | MCP server overview, tools reference, configuration |
| [mcp/QUICK_REFERENCE.md](./mcp/QUICK_REFERENCE.md) | One-page MCP cheat sheet |
| [mcp/INTEGRATION.md](./mcp/INTEGRATION.md) | Agent integration examples — Claude, Python, Azure AI |

## Guides

| File | Description |
|------|-------------|
| [guides/QUICK_START.md](./guides/QUICK_START.md) | Five-minute setup from clone to running |
| [guides/DATABASE.md](./guides/DATABASE.md) | Schema reference, seed data, migrations, common DB operations |

## Testing

| File | Description |
|------|-------------|
| [testing/TESTING.md](./testing/TESTING.md) | Running tests, test categories, manual API and MCP curl examples |

## Roadmap

| File | Description |
|------|-------------|
| [roadmap/README.md](./roadmap/README.md) | Roadmap overview — immediate backlog + completed auto-detection |
| [roadmap/PLANNED_CELLS.md](./roadmap/PLANNED_CELLS.md) | New cells: `tasks`, `references`, `errors`, `persons`, `versions` |
| [roadmap/INTELLIGENCE.md](./roadmap/INTELLIGENCE.md) | Cross-cell linking, duplicate detection, session context injection, weekly digest |
| [roadmap/INTEGRATIONS.md](./roadmap/INTEGRATIONS.md) | GitHub, Jira/Azure DevOps, Slack/Teams, Keycloak per-user memory |
| [roadmap/ADVANCED.md](./roadmap/ADVANCED.md) | Contradictie-detectie, kennisgraaf, proactieve context push, multi-agent geheugen, fine-tuning export |

---

## Where to start

**New to the project?** Start with the [Quick Start Guide](./guides/QUICK_START.md).

**Deploying?** See [Docker](./deployment/DOCKER.md) for local or [Kubernetes](./deployment/KUBERNETES.md) for production.

**Integrating with Copilot or Claude?** See the [MCP Guide](./mcp/GUIDE.md) and [Integration Examples](./mcp/INTEGRATION.md).

**API development?** See [Endpoints](./api/ENDPOINTS.md) and [Architecture](./api/ARCHITECTURE.md).

**Running tests?** See the [Testing Guide](./testing/TESTING.md).

---

## Documentation Structure

```
docs/
├── api/          ARCHITECTURE.md, ENDPOINTS.md
├── deployment/   DOCKER.md, KIND.md, KUBERNETES.md
├── guides/       QUICK_START.md, DATABASE.md
├── mcp/          GUIDE.md, QUICK_REFERENCE.md, INTEGRATION.md
├── testing/      TESTING.md
└── README.md
```


