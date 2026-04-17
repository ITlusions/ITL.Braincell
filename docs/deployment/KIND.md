# Kind — Local Kubernetes Chart Testing

Kind (Kubernetes in Docker) lets you run a real Kubernetes cluster on your local machine
to test the BrainCell Helm chart before deploying to production.

---

## Prerequisites

- Docker Desktop running
- `kind` installed: https://kind.sigs.k8s.io/docs/user/quick-start/#installation
- `kubectl` installed
- `helm` v3 installed

```powershell
# Verify tools
kind version
kubectl version --client
helm version
```

---

## Cluster Setup

### Create the Cluster

BrainCell uses a custom Kind config to expose ports on the host:

```bash
kind create cluster --name braincell --config kind-config.yaml
```

`kind-config.yaml` (project root):

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 9600       # Traefik ingress → host:9600
        protocol: TCP
      - containerPort: 50051
        hostPort: 9601       # Weaviate gRPC → host:9601
        protocol: TCP
```

### Load Images into Kind

Kind does not pull from Docker Hub by default during development.
Load locally built images into the cluster:

```bash
# Build images first
docker compose build braincell-api braincell-mcp

# Load into Kind cluster
kind load docker-image itlbraincell/api:latest --name braincell
kind load docker-image itlbraincell/mcp:latest --name braincell
```

---

## Helm Chart Deployment

### Install Dependencies

```bash
cd charts/ITL.Braincell
helm dependency update
```

This downloads the chart dependencies into `charts/`:

| Chart          | Version | Purpose              |
|----------------|---------|----------------------|
| cloudnative-pg | 0.27.1  | PostgreSQL operator  |
| weaviate       | 17.7.0  | Vector database      |
| traefik        | 26.0.0  | Ingress controller   |

### Install the Chart

```bash
helm install braincell . \
  --namespace braincell \
  --create-namespace

# Or with development values
helm install braincell . \
  --namespace braincell \
  --create-namespace \
  --values values-development.yaml
```

### Check Status

```bash
# All resources in namespace
kubectl get all -n braincell

# Pods only
kubectl get pods -n braincell

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  --all -n braincell --timeout=300s
```

### Upgrade After Changes

```bash
helm upgrade braincell . \
  --namespace braincell
```

### Uninstall

```bash
helm uninstall braincell --namespace braincell
kubectl delete namespace braincell
```

---

## Accessing Services in Kind

Because Kind runs inside Docker, services are not directly available on `localhost`.
Use port-forwarding to access them:

```bash
# REST API
kubectl port-forward -n braincell svc/braincell-api 9504:8000

# MCP Server (via Traefik ingress exposed on host port 9600)
# http://localhost:9600/mcp

# MCP Server (direct port-forward)
kubectl port-forward -n braincell svc/braincell-mcp 9506:9506

# Dashboard
kubectl port-forward -n braincell svc/braincell-dashboard 9507:8001

# pgAdmin
kubectl port-forward -n braincell svc/pgadmin 9505:80

# PostgreSQL
kubectl port-forward -n braincell svc/braincell-itl-braincell-postgres 9500:5432

# Weaviate
kubectl port-forward -n braincell svc/weaviate 9501:80
```

When Traefik is deployed, the MCP server is accessible via the Kind host port mapping:

```bash
# Via Traefik ingress (mapped to host port 9600 in kind-config.yaml)
curl http://localhost:9600/mcp

# Check Traefik routing
kubectl get ingress -n braincell
```

---

## Helm Chart Structure

```
charts/ITL.Braincell/
├── Chart.yaml                      # Chart metadata + dependency declarations
├── Chart.lock                      # Locked dependency versions
├── values.yaml                     # Default configuration values
├── values-development.yaml         # Development overrides
├── values-staging.yaml             # Staging overrides
├── values-production.yaml          # Production overrides
├── NOTES.txt                       # Post-install instructions
├── templates/
│   ├── _helpers.tpl                # Template helper functions
│   ├── namespace.yaml              # Namespace resource
│   ├── api-deployment.yaml         # REST API Deployment + Service
│   ├── mcp-deployment.yaml         # MCP Server Deployment + Service + Ingress
│   ├── postgres-*.yaml             # CloudNativePG cluster resources
│   └── ...
└── charts/
    ├── cloudnative-pg/             # Downloaded dependency
    ├── weaviate/                   # Downloaded dependency
    └── traefik/                    # Downloaded dependency
```

---

## Helm Chart Key Configuration

### MCP Server (values.yaml)

```yaml
mcp:
  enabled: true
  replicaCount: 1
  port: 9506
  image:
    repository: itlbraincell/mcp
    tag: latest
  ingress:
    enabled: true
    className: traefik
    path: /mcp
    pathType: Prefix
```

### Traefik Ingress

```yaml
traefik:
  enabled: true
  ingressClass:
    enabled: true
    isDefaultClass: true
  ports:
    web:
      port: 80
```

### Disable Ingress for Local Port-Forwarding

If you prefer direct port-forwarding over Traefik ingress:

```yaml
mcp:
  ingress:
    enabled: false

traefik:
  enabled: false
```

---

## Helm Lint and Dry Run

Before installing, validate the chart:

```bash
cd charts/ITL.Braincell

# Lint
helm lint .

# Dry run (shows rendered templates without deploying)
helm install braincell . \
  --namespace braincell \
  --create-namespace \
  --dry-run \
  --debug

# Render templates locally
helm template braincell . \
  --namespace braincell
```

---

## Teardown

```bash
# Delete the Kind cluster
kind delete cluster --name braincell

# Verify
kind get clusters
```

Deleting the cluster removes all data including volumes. Helm releases are also gone.

---

## Troubleshooting

### Pod stuck in Pending

```bash
kubectl describe pod <pod-name> -n braincell
```

Common causes:
- Image not loaded into Kind: run `kind load docker-image`
- Insufficient resources: check Docker Desktop memory allocation
- PVC not bound: check if the StorageClass is available in Kind

### ImagePullBackOff

Images tagged `latest` from local builds must be loaded into Kind before install:

```bash
kind load docker-image itlbraincell/api:latest --name braincell
kind load docker-image itlbraincell/mcp:latest --name braincell
```

Or set `imagePullPolicy: Never` in values.yaml for local development.

### Helm dependency not found

```bash
cd charts/ITL.Braincell
helm repo add traefik https://traefik.github.io/charts
helm repo add weaviate https://weaviate.github.io/weaviate-helm
helm dependency update
```

### Pod logs

```bash
kubectl logs -n braincell deployment/braincell-api
kubectl logs -n braincell deployment/braincell-mcp
kubectl logs -n braincell -l app=weaviate
```
