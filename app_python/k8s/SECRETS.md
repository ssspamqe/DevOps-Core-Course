# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating the Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
# secret/app-credentials created
```

### Viewing the Secret (YAML)

```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### Decoding Base64 Values

```bash
$ kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
admin

$ kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
supersecret123
```

### Base64 Encoding vs Encryption

| Aspect | Base64 Encoding | Encryption |
|--------|----------------|------------|
| Purpose | Transport/storage encoding | Data confidentiality |
| Reversible | Yes — trivially with `base64 -d` | Only with the key |
| Security | **None** — anyone can decode | Strong if key is protected |
| K8s default | ✅ Default for Secrets | ❌ Not enabled by default |

Kubernetes Secrets are **not encrypted** by default. The values are only base64-encoded in the etcd database. Anyone with access to the Kubernetes API or etcd can trivially decode them.

#### etcd Encryption at Rest

- By default, Kubernetes stores all Secret data in plain text inside etcd.
- **EncryptionConfiguration** can be enabled on the API server to encrypt Secret data using AES-CBC, AES-GCM, or KMS providers.
- You should enable etcd encryption at rest for any production cluster.
- Reference: [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)

---

## Task 2 — Helm-Managed Secrets

### Chart Structure with Secrets

```
app-python/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── secrets.yaml        ← new
    ├── serviceaccount.yaml ← new
    ├── deployment.yaml     ← updated
    └── service.yaml
```

### `templates/secrets.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "common.fullname" . }}-secret
  labels:
    {{- include "common.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secret.username | quote }}
  password: {{ .Values.secret.password | quote }}
```

### `values.yaml` — Secret Placeholders

```yaml
# Secret values — use --set or values override; never commit real values
secret:
  username: "app-user"
  password: "changeme"
```

> **Security note:** Only placeholder values are committed. Real secrets are supplied at deploy time with `--set secret.password=...`.

### Secret Consumed in Deployment via `envFrom`

```yaml
containers:
- name: app-python
  envFrom:
    - secretRef:
        name: {{ include "common.fullname" . }}-secret
  env:
    {{- include "common.envVars" . | nindent 10 }}
```

The `envFrom.secretRef` pattern injects **all keys** from the Secret as environment variables into the container.

### Helm-Managed Secret (kubectl get)

```yaml
apiVersion: v1
data:
  password: Y2hhbmdlbWU=
  username: YXBwLXVzZXI=
kind: Secret
metadata:
  labels:
    app.kubernetes.io/instance: app-python
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: app-python
  name: app-python-app-python-secret
  namespace: default
type: Opaque
```

### Environment Variables in Pod

Environment variables injected from the secret appear in the container environment. They are **not visible** in `kubectl describe pod` output (only the key names are shown, not values):

```bash
$ kubectl describe pod <pod-name> | grep -A5 "Environment Variables from"
Environment Variables from:
  app-python-app-python-secret  Secret  Optional: false
```

---

## Task 2 — Resource Management

### Resource Limits Configuration

```yaml
# values.yaml
resources:
  limits:
    cpu: 200m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 64Mi
```

### Requests vs Limits

| | Requests | Limits |
|---|---|---|
| **Purpose** | Minimum guaranteed resources | Maximum allowed resources |
| **Scheduling** | Kubernetes scheduler uses this to find a node | Does not affect scheduling |
| **Enforcement** | Reserved on the node | CPU: throttled; Memory: OOMKilled |
| **Best practice** | Set based on measured baseline usage | Set 2-4× the request value |

### Choosing Appropriate Values

1. **Profile** your application under load to measure actual CPU/memory usage.
2. Set **requests** equal to the 50th-percentile (normal) usage.
3. Set **limits** equal to the 95th-percentile (peak) usage to allow burst.
4. For memory-sensitive apps, keep requests ≈ limits to avoid OOMKill surprises.
5. Use `kubectl top pods` or Prometheus metrics to validate after deployment.

---

## Task 3 — HashiCorp Vault Integration

### Vault Installation

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --namespace vault \
  --create-namespace
```

### Vault Pods Running

```
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          81s
vault-agent-injector-8c76487db-5bnhx   1/1     Running   0          82s
```

### KV Secrets Engine Configuration

```bash
# KV v2 is pre-enabled in dev mode at path "secret/"
# Store app secrets
kubectl exec -n vault vault-0 -- vault kv put secret/app-python/config \
  username="app-admin" \
  password="vault-secret-456"

# Output:
# ======== Secret Path ========
# secret/data/app-python/config
# ...
# version: 1
```

### Verify Secret in Vault

```
======== Secret Path ========
secret/data/app-python/config

====== Data ======
Key         Value
---         -----
password    vault-secret-456
username    app-admin
```

### Kubernetes Authentication Configuration

```bash
# 1. Enable Kubernetes auth method
vault auth enable kubernetes

# 2. Configure with cluster address
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# 3. Create policy granting read access
vault policy write app-python - <<EOF
path "secret/data/app-python/config" {
  capabilities = ["read"]
}
EOF

# 4. Bind policy to service account
vault write auth/kubernetes/role/app-python \
  bound_service_account_names=app-python-app-python \
  bound_service_account_namespaces=default \
  policies=app-python \
  ttl=24h
```

### ServiceAccount

A dedicated ServiceAccount is provisioned by the Helm chart (`templates/serviceaccount.yaml`) so Vault can verify the pod's identity:

```bash
$ kubectl get serviceaccounts app-python-app-python
NAME                    AGE
app-python-app-python   2m22s
```

### Vault Agent Injection Annotations

Added to the pod template in `deployment.yaml`:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "app-python"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/app-python/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/app-python/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### Vault Annotations Verified on Pods

```
Annotations:  vault.hashicorp.com/agent-inject: true
              vault.hashicorp.com/agent-inject-secret-config: secret/data/app-python/config
              vault.hashicorp.com/agent-inject-template-config:
                {{- with secret "secret/data/app-python/config" -}}
                APP_USERNAME={{ .Data.data.username }}
                APP_PASSWORD={{ .Data.data.password }}
                {{- end -}}
              vault.hashicorp.com/role: app-python
```

The Vault Agent Injector mutating webhook intercepts pod creation, injects an init container that authenticates with Vault using the pod's service account JWT, fetches the secrets, and writes them to `/vault/secrets/config` inside the pod.

### Sidecar Injection Pattern

```
┌─────────────────────────────────────────────┐
│  Pod                                        │
│  ┌─────────────────┐  ┌───────────────────┐ │
│  │  vault-agent    │  │  app container    │ │
│  │  (init + sidecar│  │                   │ │
│  │   container)    │  │  /vault/secrets/  │ │
│  │                 │──▶  config           │ │
│  │  Authenticates  │  │  (rendered file)  │ │
│  │  with Vault via │  │                   │ │
│  │  K8s SA token   │  └───────────────────┘ │
│  └─────────────────┘                        │
└─────────────────────────────────────────────┘
```

1. **Init container** — `vault-agent-init` runs first, authenticates with Vault using the pod's service account JWT, and writes secrets to the shared `/vault/secrets/` volume.
2. **Sidecar container** — `vault-agent` continues running to refresh secrets when they rotate.
3. The app container reads secrets from `/vault/secrets/config` — **never touching the Vault API directly**.

---

## Bonus — Vault Agent Templates & Named Helm Templates

### Template Annotation

The `agent-inject-template-config` annotation renders secrets into a custom format instead of the default JSON:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/app-python/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders `/vault/secrets/config` as a `.env`-style file:

```
APP_USERNAME=app-admin
APP_PASSWORD=vault-secret-456
```

### Dynamic Secret Rotation

Vault Agent's sidecar continuously monitors the secret's lease. When Vault renews or rotates a secret:
1. Vault Agent renders the updated template to the file.
2. The `vault.hashicorp.com/agent-inject-command` annotation can trigger a command (e.g., `kill -HUP 1`) to signal the app to reload its configuration without a restart.

```yaml
vault.hashicorp.com/agent-inject-command-config: "kill -HUP 1"
```

### Named Templates in `_helpers.tpl` (common-lib)

A named template `common.envVars` was added to `common-lib/templates/_labels.tpl` to avoid repeating common environment variable definitions across deployments:

```yaml
{{/*
Common environment variables — DRY named template for reuse across deployments.
*/}}
{{- define "common.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment | default "production" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}
```

Used in `deployment.yaml`:

```yaml
env:
  {{- include "common.envVars" . | nindent 10 }}
```

Rendered output:

```yaml
env:
  - name: APP_ENV
    value: "production"
  - name: LOG_LEVEL
    value: "info"
```

**Benefits:**
- **DRY principle** — define once, reuse across all charts that depend on `common-lib`.
- **Consistency** — all apps share the same base env vars from a single source of truth.
- **Maintainability** — adding a new common env var requires one change in `_helpers.tpl`.

---

## Security Analysis

### K8s Secrets vs HashiCorp Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---|---|---|
| Storage | etcd (base64, optionally encrypted) | Vault's encrypted backend (AES-256-GCM) |
| Encryption at rest | Optional (EncryptionConfiguration) | Always encrypted |
| Access control | RBAC only | Fine-grained policies (path-level) |
| Secret rotation | Manual | Automatic with dynamic secrets |
| Audit logging | Limited (API server audit) | Full audit trail built-in |
| Multi-cluster | No (namespace-scoped) | Yes (namespaces, multiple backends) |
| Dynamic secrets | No | Yes (DB, AWS, PKI, etc.) |
| Secret versioning | No | Yes (KV v2) |
| Setup complexity | Simple | Moderate to complex |

### When to Use Each

**Use Kubernetes Secrets when:**
- Simple apps with few secrets
- Non-production / dev environments
- etcd encryption at rest is enabled
- You don't need secret rotation or audit trails

**Use HashiCorp Vault when:**
- Production workloads with compliance requirements
- Secrets need to be rotated automatically
- Multiple teams or clusters share secrets
- Dynamic secrets (DB credentials, cloud IAM, TLS certs) are needed
- Full audit trail is required

### Production Recommendations

1. **Always enable etcd encryption at rest** for any production cluster.
2. **Use RBAC** to restrict which service accounts can read which Secrets.
3. **Never commit real secrets** to version control — use placeholder values and override at deploy time.
4. **Prefer Vault** for production workloads; it provides encryption, rotation, audit, and more.
5. **Use the Agent Injector pattern** (not Vault SDK in app code) to keep apps decoupled from Vault.
6. **Set short TTLs** on Vault roles so compromised tokens expire quickly.
7. Consider **External Secrets Operator** as an alternative that syncs Vault/AWS/GCP secrets into K8s Secrets automatically.
