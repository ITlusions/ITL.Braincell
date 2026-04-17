# Kubernetes — Helm Deployment

This document covers deploying BrainCell to a Kubernetes cluster using Helm,
from first install through production operations.

---

## Prerequisites

| Tool      | Version  | Purpose                  |
|-----------|----------|--------------------------|
| kubectl   | 1.28+    | Cluster management       |
| Helm      | 3.12+    | Chart install / upgrade  |
| Docker    | 24+      | Image build / push       |

```bash
# Verify tools
kubectl version --client
helm version
docker version --format '{{.Client.Version}}'
```

---

## Cluster Requirements

**Minimum (development / staging)**
- 2 worker nodes, 4 vCPU / 8 GB RAM each

**Recommended (production)**
- 3+ worker nodes, 8 vCPU / 16 GB RAM each
- StorageClass with `ReadWriteOnce` (SSD preferred)
- Cloud provider LoadBalancer or MetalLB

---

## Chart Structure

```
charts/ITL.Braincell/
├── Chart.yaml              # Chart metadata + dependency declarations
├── Chart.lock              # Locked dependency versions
├── values.yaml             # Default configuration
├── values-development.yaml # Development overrides
├── values-staging.yaml     # Staging overrides
├── values-production.yaml  # Production overrides
└── templates/
    ├── _helpers.tpl
    ├── api-deployment.yaml
    ├── mcp-deployment.yaml  # MCP Deployment + Service + Ingress
    ├── postgres-*.yaml      # CloudNativePG cluster
    └── ...
```

### Chart Dependencies

| Chart          | Repository                                       | Purpose              |
|----------------|--------------------------------------------------|----------------------|
| cloudnative-pg | cloudnative-pg.github.io/charts                  | PostgreSQL operator  |
| weaviate       | weaviate.github.io/weaviate-helm                 | Vector database      |
| traefik        | traefik.github.io/charts (v26.0.0)              | Ingress controller   |

---

## First-Time Setup

### 1. Add Helm Repositories

```bash
helm repo add cloudnative-pg https://cloudnative-pg.github.io/charts
helm repo add weaviate https://weaviate.github.io/weaviate-helm
helm repo add traefik https://traefik.github.io/charts
helm repo update
```

### 2. Download Dependencies

```bash
cd charts/ITL.Braincell
helm dependency update
```

### 3. Build and Push Images

```powershell
# Build and push all images (Docker Hub)
.\build-images.ps1 -Action build-push -Version 1.0.0

# Build and push to ACR
.\build-images.ps1 -Action build-push -Version 1.0.0 `
  -Registry yourregistry.azurecr.io `
  -Repository braincell
```

### 4. Create and Apply Secrets

```powershell
# Generate secret templates
.\k8s\manage-secrets.ps1 -Action generate -Environment production

# Edit the generated files under k8s/secrets/generated/production/
# Then apply:
.\k8s\manage-secrets.ps1 -Action apply -Environment production

# Verify
.\k8s\manage-secrets.ps1 -Action validate -Environment production
```

---

## Install

### Automated (Recommended)

```powershell
.\deploy.ps1 -Action install -Environment production -Version 1.0.0 -Wait
```

### Manual

```bash
helm install braincell charts/ITL.Braincell \
  --namespace braincell \
  --create-namespace \
  --values charts/ITL.Braincell/values-production.yaml \
  --set api.image.tag=1.0.0 \
  --set mcp.image.tag=1.0.0 \
  --wait \
  --timeout 10m
```

---

## Upgrade

```powershell
# Automated upgrade
.\deploy.ps1 -Action upgrade -Environment production -Version 1.0.1 -Wait
```

```bash
# Manual upgrade
helm upgrade braincell charts/ITL.Braincell \
  --namespace braincell \
  --values charts/ITL.Braincell/values-production.yaml \
  --set api.image.tag=1.0.1 \
  --set mcp.image.tag=1.0.1 \
  --wait \
  --timeout 10m
```

---

## Rollback

```powershell
.\deploy.ps1 -Action rollback -Environment production
```

```bash
# Rollback Helm release to previous revision
helm rollback braincell -n braincell

# Rollback a specific deployment
kubectl rollout undo deployment/braincell-api -n braincell
```

---

## Verify Deployment

```bash
# All resources in namespace
kubectl get all -n braincell

# Watch pod status
kubectl get pods -n braincell -w

# Ingress routes
kubectl get ingress -n braincell

# HPA status
kubectl get hpa -n braincell
```

---

## Port-Forward Access

During development or debugging, forward service ports to localhost:

```bash
# REST API (internal 8000)
kubectl port-forward -n braincell svc/braincell-api 9504:8000

# MCP Server (internal 9506)
kubectl port-forward -n braincell svc/braincell-mcp 9506:9506

# Dashboard (internal 8001)
kubectl port-forward -n braincell svc/braincell-dashboard 9507:8001

# PostgreSQL (internal 5432)
kubectl port-forward -n braincell svc/braincell-postgres 9500:5432

# Weaviate (internal 80)
kubectl port-forward -n braincell svc/weaviate 9501:80
```

---

## Traefik Ingress

The chart installs Traefik as the ingress controller.
The MCP server is routed under `/mcp`:

| Path    | Service          | Port |
|---------|------------------|------|
| `/mcp`  | braincell-mcp    | 9506 |
| `/`     | braincell-api    | 8000 |

Check the external IP assigned to Traefik:

```bash
kubectl get svc -n braincell traefik
```

Configure DNS to point your domain to the LoadBalancer IP, then update `values-production.yaml`:

```yaml
mcp:
  ingress:
    hosts:
      - host: braincell.yourdomain.com
        paths:
          - path: /mcp
            pathType: Prefix
    tls:
      enabled: true
      secretName: braincell-tls
```

---

## Values Files

### Production (`values-production.yaml`)

Key settings for production:

```yaml
api:
  replicaCount: 3
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

mcp:
  enabled: true
  replicaCount: 2
  port: 9506

cnpg:
  instances: 3
  storage:
    size: 50Gi
    storageClass: "premium-rwo"
  backup:
    enabled: true
    schedule: "0 2 * * *"
    retentionPolicy: "30d"

monitoring:
  enabled: true
```

### Staging (`values-staging.yaml`)

Single replicas, smaller storage, monitoring off.

### Development (`values-development.yaml`)

Single replicas, no autoscaling, debug logging.

---

## Automation Scripts

### `deploy.ps1`

```powershell
# Available actions
.\deploy.ps1 -Action install   -Environment production -Version 1.0.0 -Wait
.\deploy.ps1 -Action upgrade   -Environment production -Version 1.0.1 -Wait
.\deploy.ps1 -Action uninstall -Environment production
.\deploy.ps1 -Action status    -Environment production
.\deploy.ps1 -Action rollback  -Environment production
```

### `build-images.ps1`

```powershell
# Build and push all components
.\build-images.ps1 -Action build-push -Component all -Version 1.0.0

# Build specific component
.\build-images.ps1 -Action build-push -Component api -Version 1.0.0
.\build-images.ps1 -Action build-push -Component mcp -Version 1.0.0
```

### `k8s/manage-secrets.ps1`

```powershell
.\k8s\manage-secrets.ps1 -Action generate -Environment production
.\k8s\manage-secrets.ps1 -Action apply    -Environment production
.\k8s\manage-secrets.ps1 -Action validate -Environment production
```

---

## Scaling

```bash
# Manual horizontal scaling
kubectl scale deployment braincell-api -n braincell --replicas=5

# Check HPA
kubectl get hpa -n braincell
kubectl describe hpa braincell-api -n braincell
```

---

## Logs

```bash
kubectl logs -n braincell -l app=braincell-api --tail=100
kubectl logs -n braincell -l app=braincell-mcp --tail=100
kubectl logs -n braincell -l app=weaviate --tail=100

# Follow in real time
kubectl logs -n braincell deployment/braincell-api -f
```

---

## Backup and Recovery

### PostgreSQL Manual Backup

```bash
kubectl exec -n braincell braincell-postgres-1 -- \
  pg_dump -U braincell braincell > braincell-backup-$(date +%Y%m%d).sql
```

### PostgreSQL Restore

```bash
kubectl exec -i -n braincell braincell-postgres-1 -- \
  psql -U braincell braincell < braincell-backup-20260417.sql
```

### Weaviate Backup

```bash
kubectl exec -n braincell weaviate-0 -- \
  tar czf /tmp/weaviate-backup.tar.gz /var/lib/weaviate
kubectl cp braincell/weaviate-0:/tmp/weaviate-backup.tar.gz \
  ./weaviate-backup-$(date +%Y%m%d).tar.gz
```

---

## Troubleshooting

### Pods in CrashLoopBackOff

```bash
kubectl describe pod <pod-name> -n braincell
kubectl logs <pod-name> -n braincell --previous
```

### ImagePullBackOff

Confirm the image tag exists in the registry and that pull credentials are configured:

```bash
kubectl get secret -n braincell | grep registry
```

### PostgreSQL Cluster Not Ready

CNPG operator takes ~2 minutes to initialize the cluster.
Check the cluster status:

```bash
kubectl get cluster -n braincell
kubectl describe cluster braincell-postgres -n braincell
```

### PVC Pending

The StorageClass might not exist or have no available capacity:

```bash
kubectl get storageclass
kubectl describe pvc -n braincell
```

### Helm Release Stuck

```bash
# Check Helm history
helm history braincell -n braincell

# Force rollback to last good revision
helm rollback braincell <revision> -n braincell
```

---

## Uninstall

```powershell
.\deploy.ps1 -Action uninstall -Environment production
```

```bash
helm uninstall braincell -n braincell
kubectl delete namespace braincell
```

This removes all Kubernetes resources but **does not** delete Persistent Volume Claims.
To delete data:

```bash
kubectl delete pvc --all -n braincell
```
