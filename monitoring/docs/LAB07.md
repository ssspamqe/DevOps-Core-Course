# Lab 7 — Observability & Logging with Loki Stack

This folder contains the monitoring stack for Lab 7 (Loki, Promtail, Grafana) and basic instructions.

Files added:

- `docker-compose.yml` — Compose stack for Loki, Promtail, Grafana, and the Python app.
- `loki/config.yml` — Loki configuration (TSDB + filesystem, 7d retention).
- `promtail/config.yml` — Promtail configuration (docker SD, relabeling to `app` and `container`).

Quick start (run from `monitoring`):

```bash
docker compose up -d
docker compose ps
curl http://localhost:3100/ready
curl http://localhost:9080/metrics
open http://localhost:3000
```

Next steps for you:

- Verify Grafana -> add Loki data source (URL: http://loki:3100)
- Generate traffic against the Python app: `for i in {1..20}; do curl http://localhost:8000/; done`
- Take screenshots of Grafana Explore showing logs from the Python app.

When you have screenshots or other input evidence, upload them into the repo under `monitoring/docs/screenshots/` and tell me — I'll pause until you provide them.
