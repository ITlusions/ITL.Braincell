# Docker — Local Development

This document covers running BrainCell locally using Docker Compose.

---

## Prerequisites

- Docker Desktop 4.x or Docker Engine 24+ with Compose v2
- 4 GB RAM available for Docker

---

## Port Mapping

| Container     | External Port | Internal Port | Purpose                  |
|---------------|---------------|---------------|--------------------------|
| PostgreSQL    | 9500          | 5432          | Database                 |
| Weaviate HTTP | 9501          | 8080          | Vector search REST API   |
| Weaviate gRPC | 9502          | 50051         | Vector search gRPC       |
| Redis         | 9503          | 6379          | Cache                    |
| REST API      | 9504          | 8000          | BrainCell REST API       |
| pgAdmin       | 9505          | 80            | Database admin UI        |
| MCP Server    | 9506          | 9506          | MCP protocol interface   |
| Dashboard     | 9507          | 8001          | Web UI                   |

---

## Quick Start

```bash
# Start all services
docker compose up -d

# Verify all containers are running
docker compose ps

# Follow logs
docker compose logs -f braincell-api
```

Services that depend on each other start in the correct order automatically via `depends_on` with health checks.

---

## Service Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: braincell-postgres
    environment:
      POSTGRES_DB: braincell
      POSTGRES_USER: braincell
      POSTGRES_PASSWORD: braincell_dev_password
    ports:
      - "9500:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U braincell"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:1.27.0
    container_name: braincell-weaviate
    ports:
      - "9501:8080"
      - "9502:50051"
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      ENABLE_API_AUTH: 'false'
    volumes:
      - weaviate_data:/var/lib/weaviate

  redis:
    image: redis:7-alpine
    container_name: braincell-redis
    ports:
      - "9503:6379"
    volumes:
      - redis_data:/data

  braincell-api:
    build:
      context: .
      dockerfile: src/api/Dockerfile
    container_name: braincell-api
    ports:
      - "9504:8000"
    environment:
      DATABASE_URL: "postgresql://braincell:braincell_dev_password@postgres:5432/braincell"
      WEAVIATE_URL: "http://weaviate:8080"
      REDIS_URL: "redis://redis:6379"
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      weaviate:
        condition: service_started

  braincell-mcp:
    build:
      context: .
      dockerfile: mcp/Dockerfile
    container_name: braincell-mcp
    ports:
      - "9506:9506"
    environment:
      DATABASE_URL: "postgresql://braincell:braincell_dev_password@postgres:5432/braincell"
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy

  braincell-dashboard:
    build:
      context: .
      dockerfile: src/web/Dockerfile
    container_name: braincell-dashboard
    ports:
      - "9507:8001"
    environment:
      DATABASE_URL: "postgresql://braincell:braincell_dev_password@postgres:5432/braincell"
      WEAVIATE_URL: "http://weaviate:8080"
      REDIS_URL: "redis://redis:6379"
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: braincell-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "9505:80"
    depends_on:
      - postgres
```

### docker-compose.override.example.yml

Create `docker-compose.override.yml` to customize for your local environment:

```yaml
version: '3.8'

services:
  braincell-api:
    environment:
      LOG_LEVEL: debug
    volumes:
      - ./src:/app/src  # hot reload

  braincell-mcp:
    environment:
      LOG_LEVEL: debug
```

---

## Health Checks

```bash
# API health
curl http://localhost:9504/health

# MCP health
curl http://localhost:9506/health

# Weaviate health
curl http://localhost:9501/v1/.well-known/ready

# PostgreSQL
docker exec braincell-postgres pg_isready -U braincell

# Redis
docker exec braincell-redis redis-cli ping
```

---

## pgAdmin

Open http://localhost:9505 and log in:

- Email: `admin@example.com`
- Password: `admin`

Add a new server:

| Field    | Value                       |
|----------|-----------------------------|
| Host     | `postgres`                  |
| Port     | `5432` (internal)           |
| Database | `braincell`                 |
| Username | `braincell`                 |
| Password | `braincell_dev_password`    |

---

## Logs

```bash
# All services
docker compose logs -f

# Single service
docker compose logs -f braincell-api
docker compose logs -f braincell-mcp

# Last 100 lines
docker compose logs --tail=100 braincell-api
```

---

## Stopping and Cleaning Up

```bash
# Stop all containers (keep volumes)
docker compose down

# Stop and remove volumes (wipes all data)
docker compose down -v

# Rebuild images after code changes
docker compose build braincell-api
docker compose up -d braincell-api

# Rebuild all images
docker compose build
docker compose up -d
```

---

## Common Issues

### Port conflict

If a port is already in use, Docker Compose will fail to start.

```bash
# Find what is using port 9504
netstat -an | findstr 9504       # Windows
lsof -i :9504                   # Linux / macOS
```

Update the port mapping in `docker-compose.override.yml` to use a different host port.

### Weaviate fails to start

Weaviate sometimes fails on first startup due to a timeout in the RAFT bootstrap:

```bash
docker compose restart weaviate
```

### API cannot connect to PostgreSQL

Ensure PostgreSQL has finished initializing before the API starts:

```bash
docker compose logs postgres | tail -20
```

If the healthcheck keeps failing, confirm that `init.sql` exists in the project root.

### Database schema missing

If the database schema is missing, run the init script manually:

```bash
docker exec -i braincell-postgres psql -U braincell -d braincell < init.sql
```

### Weaviate sync out of date

If the vector index is stale compared to PostgreSQL, trigger a full re-sync:

```bash
curl -X POST http://localhost:9504/admin/sync
```

---

## Environment Variables

These environment variables can be set in `docker-compose.override.yml` or `.env`:

| Variable       | Default                                                           | Description               |
|----------------|-------------------------------------------------------------------|---------------------------|
| DATABASE_URL   | `postgresql://braincell:braincell_dev_password@postgres:5432/braincell` | PostgreSQL connection |
| WEAVIATE_URL   | `http://weaviate:8080`                                            | Weaviate HTTP endpoint    |
| REDIS_URL      | `redis://redis:6379`                                              | Redis connection          |
| ENVIRONMENT    | `development`                                                     | App environment flag      |
| LOG_LEVEL      | `info`                                                            | Logging level             |
