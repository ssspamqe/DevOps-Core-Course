# ArgoCD Documentation

## 1. ArgoCD Setup

ArgoCD was installed into a dedicated `argocd` namespace from the official Helm repository:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd
```

Installation was verified by checking the ArgoCD CRDs and controller pods:

```bash
kubectl get crd applications.argoproj.io applicationsets.argoproj.io
kubectl get pods -n argocd
```

The important result was that both ArgoCD CRDs existed and the long-lived ArgoCD components were running:

```text
NAME                          CREATED AT
applications.argoproj.io      2026-04-23T20:29:30Z
applicationsets.argoproj.io   2026-04-23T20:29:30Z
```

Access to the web UI was provided through port forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The UI is available at:

```text
https://localhost:8080
```

The initial admin password can be retrieved with:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

The ArgoCD CLI was installed locally to `~/.local/bin/argocd` because Homebrew could not write to `/opt/homebrew` in this environment. CLI access was configured with:

```bash
export PATH="$HOME/.local/bin:$PATH"
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d)
argocd login localhost:8080 --username admin --password "$ARGOCD_PASSWORD" --insecure
```

The installed CLI version was:

```text
argocd: v3.3.8+7ae7d2c
```

## 2. Application Configuration

ArgoCD manifests are stored in `app_python/k8s/argocd/`:

- `application.yaml`
- `application-dev.yaml`
- `application-prod.yaml`
- `applicationset.yaml`

All three Application manifests use the same Helm chart source:

```yaml
repoURL: https://github.com/ssspamqe/DevOps-Core-Course.git
targetRevision: lab12
path: app_python/k8s/app-python
```

`targetRevision` is set to `lab12` instead of `lab13` because the remote repository did not contain a `lab13` branch yet, and `origin/master` did not contain the Helm chart path. `origin/lab12` was the newest remote branch that actually contained `app_python/k8s/app-python`, so ArgoCD had to track that branch to sync successfully.

Environment-specific configuration:

| Application | Namespace | Values file | Sync policy |
| --- | --- | --- | --- |
| `app-python` | `default` | `values.yaml` | Manual |
| `app-python-dev` | `dev` | `values-dev.yaml` | Automated with `prune` and `selfHeal` |
| `app-python-prod` | `prod` | `values-prod.yaml` | Manual |

The dev application manifest contains:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

The default and prod applications keep only:

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
```

This matches the intended workflow:

- `dev` is fully automated for quick feedback and drift correction.
- `prod` remains manual so releases can be reviewed and triggered explicitly.

## 3. Multi-Environment Deployment

Separate namespaces were used for the environments:

```bash
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
```

After applying the Application manifests and syncing them, the workloads reflected the Helm values files correctly:

```text
NAME                    CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH       SYNCPOLICY  REPO                                                PATH                       TARGET
argocd/app-python       https://kubernetes.default.svc  default    default  Synced  Healthy      Manual      https://github.com/ssspamqe/DevOps-Core-Course.git  app_python/k8s/app-python  lab12
argocd/app-python-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy      Auto-Prune  https://github.com/ssspamqe/DevOps-Core-Course.git  app_python/k8s/app-python  lab12
argocd/app-python-prod  https://kubernetes.default.svc  prod       default  Synced  Progressing  Manual      https://github.com/ssspamqe/DevOps-Core-Course.git  app_python/k8s/app-python  lab12
```

The environment differences matched the values files:

```text
default:
deployment.apps/app-python-app-python   3/3
service/app-python-app-python           ClusterIP

dev:
deployment.apps/app-python-dev-app-python   1/1
service/app-python-dev-app-python           NodePort

prod:
deployment.apps/app-python-prod-app-python   3/3
service/app-python-prod-app-python           LoadBalancer
```

In Minikube, the prod service stayed `Progressing` from ArgoCD's point of view because `LoadBalancer` services keep `EXTERNAL-IP` as `<pending>` unless `minikube tunnel` is used. The deployment and pods themselves were healthy:

```text
app-python-prod-app-python-64c8997696-9ddn7   1/1   Running
app-python-prod-app-python-64c8997696-gqn7c   1/1   Running
app-python-prod-app-python-64c8997696-x7rfs   1/1   Running
```

## 4. Self-Healing Evidence

### 4.1 Manual Scale Test

The dev deployment was manually scaled away from the Git state:

```bash
kubectl scale deployment app-python-dev-app-python -n dev --replicas=5
kubectl wait --for=jsonpath='{.spec.replicas}'=1 deployment/app-python-dev-app-python -n dev --timeout=180s
```

Observed output:

```text
before-scale 2026-04-23 23:36:31 MSK
1|1
deployment.apps/app-python-dev-app-python scaled
after-manual-scale 2026-04-23 23:36:31 MSK
5|1
deployment.apps/app-python-dev-app-python condition met
after-self-heal 2026-04-23 23:36:31 MSK
1|1
```

Result: ArgoCD detected that the live deployment no longer matched Git and automatically restored the replica count to `1` because `selfHeal: true` was enabled for `app-python-dev`.

### 4.2 Pod Deletion Test

One running pod in the dev namespace was deleted manually:

```bash
kubectl delete pod -n dev <pod-name>
kubectl rollout status deployment/app-python-dev-app-python -n dev --timeout=120s
```

Observed output:

```text
clean-pod-delete 2026-04-23 23:37:38 MSK
replicas-before 1|1
app-python-dev-app-python-8fd69c4fc-bt7lx   Running
pod "app-python-dev-app-python-8fd69c4fc-bt7lx" deleted from dev namespace
deployment "app-python-dev-app-python" successfully rolled out
after-running-pod-recreated 2026-04-23 23:38:00 MSK
app-python-dev-app-python-8fd69c4fc-8kdtb   Running
replicas-after 1|1
```

Result: this recovery was Kubernetes behavior, not ArgoCD behavior. The Deployment/ReplicaSet controller recreated the missing pod to maintain the desired replica count.

### 4.3 Configuration Drift Test

Adding ad-hoc labels with a merge patch was not a reliable proof in this setup because those labels were preserved. A stricter managed field was used instead: the deployment image was manually changed from the Git-defined application image to `nginx:latest`.

```bash
kubectl set image deployment/app-python-dev-app-python -n dev app-python=nginx:latest
kubectl wait --for=jsonpath='{.spec.template.spec.containers[0].image}'='ssspamqe/devops-info-service:latest' \
  deployment/app-python-dev-app-python -n dev --timeout=180s
```

Observed output:

```text
image-before 2026-04-23 23:39:18 MSK
ssspamqe/devops-info-service:latest
deployment.apps/app-python-dev-app-python image updated
image-after-manual 2026-04-23 23:39:18 MSK
nginx:latest
deployment.apps/app-python-dev-app-python condition met
image-after-self-heal 2026-04-23 23:39:19 MSK
ssspamqe/devops-info-service:latest
```

Result: ArgoCD automatically reverted the configuration drift and restored the image from Git.

### 4.4 Sync Behavior Summary

- Kubernetes self-healing recreates missing pods to satisfy the Deployment spec already stored in the cluster.
- ArgoCD self-healing changes the cluster spec itself so that it matches Git again.
- ArgoCD polls Git every 3 minutes by default.
- Sync can also be triggered manually through the UI or CLI.
- Webhooks can be added later for near-immediate Git change detection.

## 5. GitOps Workflow Note

The declarative ArgoCD deployment worked correctly from Git, but the full "commit to current branch and watch ArgoCD detect it" demonstration was limited by the remote repository state:

- local work was done in `lab13`
- `origin/lab13` did not exist yet
- `origin/master` was too old and did not contain `app_python/k8s/app-python`
- `origin/lab12` was the latest remote branch that ArgoCD could actually use

To demonstrate Git-based change pickup on the current lab branch, push `lab13` to the remote repository and then change `targetRevision` from `lab12` to `lab13` in the ArgoCD manifests.

## 6. Bonus: ApplicationSet

`app_python/k8s/argocd/applicationset.yaml` contains a bonus `ApplicationSet` implementation using a List generator.

It defines two environments:

- `dev` with `values-dev.yaml` and auto-sync enabled
- `prod` with `values-prod.yaml` and manual sync

The manifest uses `goTemplate` and `templatePatch` so that only the dev application receives the automated sync block. It was not applied on top of the live cluster state because the individual `Application` manifests with the same ArgoCD application names were already being used.

Benefits of this pattern:

- one template can generate multiple environment applications
- environment parameters stay centralized in one manifest
- it scales better than hand-maintaining many similar `Application` resources

## 7. Screenshots

Create the required screenshots in `app_python/docs/screenshots/lab13/`.

Recommended files:

- `argocd-app-list.png` — ArgoCD UI showing all applications
- `argocd-app-dev-details.png` — details page for `app-python-dev`
- `argocd-sync-status.png` — sync/health statuses after deployment

They can be referenced from this document later with standard Markdown image links after the screenshots are captured.