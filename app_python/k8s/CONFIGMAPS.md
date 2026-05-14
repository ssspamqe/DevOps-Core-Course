# ConfigMaps & Persistent Volumes

## Application Changes

### Visits Counter Implementation

The application was extended with a file-based visit counter:

- Each request to `/` increments a counter stored in `/data/visits`
- Atomic writes via a temp file + `os.replace()` prevent corruption
- Thread-safe access is ensured with `threading.Lock`
- Counter defaults to `0` if the file does not exist

### New Endpoint: `/visits`

```
GET /visits
```

Returns the current visit count:

```json
{"visits": 12}
```

### Local Testing with Docker

`docker-compose.yml` mounts a host volume for persistence:

```yaml
volumes:
  - ./data:/data
```

Verification:

```bash
$ curl -s http://localhost:8080/visits
{"visits": 0}

$ curl -s http://localhost:8080/ > /dev/null
$ curl -s http://localhost:8080/ > /dev/null

$ curl -s http://localhost:8080/visits
{"visits": 2}

$ docker compose restart
$ curl -s http://localhost:8080/visits
{"visits": 2}   # Counter survived restart
```

---

## ConfigMap Implementation

### ConfigMap for File Mounting (`configmap.yaml`)

Loads `files/config.json` into a ConfigMap and mounts it at `/config/config.json`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

**`files/config.json` content:**

```json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visits_counter": true,
    "metrics": true,
    "health_check": true
  },
  "log_format": "json"
}
```

### ConfigMap for Environment Variables (`configmap-env.yaml`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
```

### Mounting in Deployment

ConfigMap as a volume:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "common.fullname" . }}-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

Environment variables via `envFrom`:

```yaml
envFrom:
  - configMapRef:
      name: {{ include "common.fullname" . }}-env
```

### Verification

```
$ kubectl exec <pod> -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visits_counter": true,
    "metrics": true,
    "health_check": true
  },
  "log_format": "json"
}

$ kubectl exec <pod> -- printenv | grep -E 'APP_ENV|LOG_LEVEL'
APP_ENV=production
LOG_LEVEL=info
```

---

## Persistent Volume

### PVC Configuration (`pvc.yaml`)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "common.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

- **Access mode**: `ReadWriteOnce` — the volume can be mounted as read-write by a single node
- **Storage class**: Uses the default Minikube `standard` storage class, which provisions hostPath volumes automatically
- **Size**: `100Mi` (configurable via `values.yaml`)

### Volume Mount in Deployment

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "common.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### Persistence Test

```
$ kubectl exec <pod> -- wget -qO- http://127.0.0.1:8080/visits
{"visits":9}

$ kubectl delete pod <pod-name>
pod "app-python-app-python-69668498f7-q5t5j" deleted

$ kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=app-python

$ kubectl exec <new-pod> -- wget -qO- http://127.0.0.1:8080/visits
{"visits":9}    # Counter survived pod deletion!
```

### Resource Overview

```
$ kubectl get configmap,pvc
NAME                                     DATA   AGE
configmap/app-python-app-python-config   1      17s
configmap/app-python-app-python-env      2      17s

NAME                                               STATUS   VOLUME       CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/app-python-app-python-data   Bound    pvc-...      100Mi      RWO            standard
```

---

## ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Purpose** | Non-sensitive configuration (env names, feature flags, log levels) | Sensitive data (passwords, API keys, TLS certs) |
| **Encoding** | Plain text | Base64-encoded at rest |
| **Encryption** | Not encrypted | Can be encrypted at rest with EncryptionConfiguration |
| **Size limit** | 1 MiB | 1 MiB |
| **Access control** | Standard RBAC | Should have stricter RBAC |
| **Use when** | App config, feature flags, URLs | Database passwords, OAuth tokens, SSH keys |

---

## Bonus: ConfigMap Hot Reload

### Default Update Behavior

When a ConfigMap is updated, Kubernetes eventually propagates changes to mounted volumes. The delay depends on:
- Kubelet sync period (default ~60s)
- ConfigMap cache TTL

Total delay can be up to **a few minutes**.

### `subPath` Limitation

When using `subPath` mounts, the file is a **copy**, not a symlink. It does **not** receive automatic updates. Use full directory mounts for auto-updates.

### Checksum Annotation Pattern (Implemented)

The deployment includes checksum annotations that trigger pod restarts when ConfigMap content changes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/config-env: {{ include (print $.Template.BasePath "/configmap-env.yaml") . | sha256sum }}
```

On `helm upgrade`, if the ConfigMap content changes, the checksum annotation changes, which causes the Deployment to create new pods — effectively a rolling restart with the new configuration.
