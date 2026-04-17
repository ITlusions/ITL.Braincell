# ITL.Braincell Helm chart

Umbrella chart to deploy the Braincell stack using CloudNativePG (CNPG) and the Weaviate Operator.

What this deploys
- A `Namespace` (default: `braincell`)
- A CloudNativePG `Cluster` CR (requires CNPG operator installed or enabled via Helm dependency)
- A Weaviate CustomResource (requires `weaviate-operator` to be installed — this chart references a local subchart `../weaviate-operator`)
- A simple `braincell-api` Deployment + Service

Requirements
- Helm 3
- If you want the CNPG operator installed by Helm, run `helm dependency update` to fetch the `cloudnative-pg` chart.
- The `weaviate-operator` chart is included as a local chart dependency in `charts/weaviate-operator` — keep it present before installing.

- This chart now depends on the official Weaviate Helm chart from `https://weaviate.github.io/weaviate-helm`.
	Add the repo and update dependencies before installing:

```sh
helm repo add semitechnologies https://weaviate.github.io/weaviate-helm
helm repo update
helm dependency update charts/ITL.Braincell
helm install braincell charts/ITL.Braincell --namespace braincell --create-namespace
```

Quick install (kind or real cluster)

```sh
# from repository root
cd d:/repos/ITL.BrainCell
helm dependency update charts/ITL.Braincell
helm install braincell charts/ITL.Braincell --namespace braincell --create-namespace
```

Notes
- The CNPG Cluster CR included here is minimal; tune the `values.yaml` storage and instance settings for production.
- The Weaviate CR is a placeholder — adapt the fields to the operator's real CRD.
