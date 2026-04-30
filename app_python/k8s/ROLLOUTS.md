# Lab 14 Report - Progressive Delivery with Argo Rollouts

## 1. Overview

In this lab I replaced the Lab 13 Helm-based `Deployment` for the Python application with Argo Rollouts and implemented two progressive delivery strategies on `minikube`:

- canary deployment with staged progression and manual promotion at the first pause
- blue-green deployment with separate active and preview services
- automated health analysis for the canary rollout using an `AnalysisTemplate`

The work was completed on the existing chart in `app_python/k8s/app-python` and validated against a running local `minikube` cluster.

## 2. Environment and Setup

The cluster used for the lab was `minikube`. Argo Rollouts controller and dashboard were installed into a dedicated `argo-rollouts` namespace. Because Homebrew could not write to `/opt/homebrew` in this environment, the Rollouts CLI plugin was installed into `$HOME/.local/bin` instead of using Homebrew.

Installation was verified by checking:

- running controller and dashboard pods in `argo-rollouts`
- presence of the `rollouts.argoproj.io` and `analysistemplates.argoproj.io` CRDs
- successful output from `kubectl-argo-rollouts version`

The dashboard was exposed locally with port-forwarding on `http://localhost:3100`.

## 3. Rollout vs Deployment

The original chart from Lab 13 used a standard Kubernetes `Deployment`. For this lab, the chart was changed so that progressive delivery is handled by an Argo `Rollout` resource by default, while the old `Deployment` template remains available as a fallback when `rollout.enabled=false`.

Compared with a regular `Deployment`, the `Rollout` added:

- a strategy block with either `canary` or `blueGreen`
- pause steps and progressive traffic or replica-weight shifting
- active and preview service switching for blue-green releases
- analysis support through `AnalysisTemplate`
- rollout-specific lifecycle operations such as promote, abort, retry, and undo

## 4. Helm Chart Implementation

The implementation was added directly to the existing Helm chart rather than creating separate handwritten manifests.

Main chart changes:

- `templates/rollout.yaml` was added to render an Argo Rollout
- `templates/analysis-template.yaml` was added for web-based canary health analysis
- `templates/service.yaml` was extended to support blue-green preview service handling
- `templates/_helpers.tpl` was added for preview service and analysis template naming
- `templates/deployment.yaml` was kept only as a fallback path when rollouts are disabled
- `values-canary.yaml` was added for canary-specific configuration
- `values-bluegreen.yaml` was added for blue-green-specific configuration

The chart kept the existing persistence, probes, config maps, and secrets from earlier labs, so the rollout strategies operated on the real application rather than on a simplified demo workload.

## 5. Canary Strategy

### 5.1 Configuration

The canary rollout used five replicas so the intended `20%`, `40%`, `60%`, and `80%` progression mapped cleanly in `minikube` without requiring a service mesh or ingress traffic manager.

The configured canary flow was:

1. set weight to `20%`
2. pause manually
3. run automated analysis against `/health`
4. set weight to `40%` and pause for `30s`
5. set weight to `60%` and pause for `30s`
6. set weight to `80%` and pause for `30s`
7. set weight to `100%`

### 5.2 AnalysisTemplate

For the bonus part of the lab, a web-based `AnalysisTemplate` was integrated into the canary strategy. It queried `http://<service>.<namespace>.svc.cluster.local/health` and evaluated the JSON field `status`.

The success condition was:

- `result == 'healthy'`

During the recorded rollout, the analysis run completed successfully with three successful checks before the rollout was later aborted to demonstrate rollback behavior.

### 5.3 Observed Result

After updating the release with a changed `environment` value, the canary rollout paused at the first `20%` step as expected. The rollout was then promoted manually and continued through the configured sequence. After that, an abort was triggered to test rollback.

Observed final canary state:

- rollout status: `Degraded`
- message: `RolloutAborted: Rollout aborted update to revision 2`
- stable ReplicaSet remained healthy and served all traffic
- canary ReplicaSet was scaled down after abort

This final state is expected for the rollback demonstration and serves as evidence that the stable version was restored successfully.

## 6. Blue-Green Strategy

### 6.1 Configuration

The blue-green rollout used:

- active service: `app-python-bluegreen-app-python`
- preview service: `app-python-bluegreen-app-python-preview`
- `autoPromotionEnabled: false`

This configuration kept the new revision behind the preview service until manual promotion was performed.

### 6.2 Observed Result

The blue-green release was installed first, then updated with a changed `environment` value to create a new revision. The dashboard showed the preview-side ReplicaSet and the preview service before promotion. The preview and active services were exposed locally with port-forwarding and were checked separately.

After manual promotion, the active service switched to the new ReplicaSet immediately. This confirmed the expected blue-green behavior: production traffic moved from old to new version in one step rather than progressively.

Observed final blue-green state:

- rollout status: `Healthy`
- desired replicas: `3`
- available replicas: `3`
- active ReplicaSet remained healthy after promotion
- previous revision was scaled down

## 7. Rollback Behavior

Two rollback models were demonstrated:

- canary rollback by aborting an in-progress rollout
- blue-green rollback capability through service switching behavior

The canary rollback clearly showed the advantage of progressive delivery: the new revision never fully replaced the stable version before the abort occurred, and traffic returned to the old stable ReplicaSet.

The blue-green strategy demonstrated instant cutover behavior. Even though only promotion was captured in the final evidence set, the rollout configuration supports immediate reversal by switching the active service back to the previous stable ReplicaSet.

## 8. Evidence

Screenshots were added to `app_python/docs/screenshots/lab14/`.

Canary evidence:

- `canary-paused-20.png` - rollout paused at the first canary step
- `canary-after-promote.png` - rollout after manual promotion
- `canary-aborted.png` - aborted canary and rollback to stable

Blue-green evidence:

- `bluegreen-dashboard.png` - dashboard view of the blue-green rollout
- `bluegreen-preview.png` - preview service exposed on `localhost:8081`
- `bluegreen-active.png` - active service exposed on `localhost:8080`
- `bluegreen-after-promote.png` - rollout after promotion

## 9. Useful Commands Used

The following commands were used during validation:

```bash
kubectl get rollout -A
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
kubectl port-forward svc/app-python-bluegreen-app-python -n default 8080:80
kubectl port-forward svc/app-python-bluegreen-app-python-preview -n default 8081:80

"$HOME/.local/bin/kubectl-argo-rollouts" version
"$HOME/.local/bin/kubectl-argo-rollouts" get rollout app-python-canary-app-python -n default
"$HOME/.local/bin/kubectl-argo-rollouts" get rollout app-python-bluegreen-app-python -n default
"$HOME/.local/bin/kubectl-argo-rollouts" promote app-python-canary-app-python -n default
"$HOME/.local/bin/kubectl-argo-rollouts" abort app-python-canary-app-python -n default
"$HOME/.local/bin/kubectl-argo-rollouts" promote app-python-bluegreen-app-python -n default
```

Helm releases were installed with `--no-hooks` in this environment because the old pre-install and post-install hook jobs were unrelated to the rollout task and slowed local validation.

## 10. Strategy Comparison

Based on the implementation and observed behavior:

- canary is better when gradual exposure and controlled risk reduction are required
- blue-green is better when a full preview environment and instant switchover are more important than gradual progression

Advantages of canary:

- safer for production changes because only part of the traffic is exposed initially
- supports metric-based gating and rollback decisions
- gives time to inspect behavior at intermediate stages

Advantages of blue-green:

- simpler to reason about operationally
- supports explicit preview validation before promotion
- promotion and rollback are effectively immediate from a traffic perspective

Disadvantages observed:

- canary takes longer to complete because of pauses and analysis steps
- blue-green requires duplicate live capacity during rollout

For this application, I would use canary for routine production updates and blue-green for changes that require explicit preview approval before switching user traffic.

## 11. Conclusion

Lab 14 was completed successfully on `minikube`.

The application chart was converted from a standard `Deployment` model to Argo Rollouts with both canary and blue-green strategies. A bonus health-based `AnalysisTemplate` was also integrated into the canary flow. The recorded evidence shows:

- canary pause and manual promotion
- successful canary analysis
- canary abort and rollback to the stable version
- blue-green preview and active service separation
- blue-green promotion and healthy final state

This lab demonstrated how progressive delivery can reduce deployment risk compared with a regular rolling update while still fitting into the same Helm-based GitOps workflow used in earlier labs.