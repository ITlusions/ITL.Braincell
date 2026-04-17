# weaviate-operator Helm chart

This chart deploys the Weaviate Operator into a Kubernetes cluster (works in kind and real clusters).

Quick start

1. Create a namespace (optional):

```sh
kubectl create namespace braincell
```

2. Install CRDs (the chart includes a placeholder under `crds/` — replace with upstream CRDs for production):

```sh
kubectl apply -f charts/weaviate-operator/crds/weaviate_crd.yaml
```

3. Install via Helm:

```sh
helm install my-weav-operator charts/weaviate-operator --namespace braincell
```

Testing in kind

1. Create a kind cluster if you don't have one:

```sh
kind create cluster --name weaviate-test
```

2. Then follow the install steps above.

Notes
- Replace the placeholder CRD with the official CRD from the operator repository before using in production.
- Customize image/tag in `values.yaml`.
