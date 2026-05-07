# Lab 7 — Observability & Logging with Loki Stack


We deploy a lightweight logging stack using Grafana Loki (TSDB + filesystem), Promtail for log collection, and Grafana for visualization. The Python app from earlier labs is attached to the same compose stack and logs in structured JSON so it can be parsed in Loki.

Configuration highlights
---
- Loki: uses `tsdb` with `filesystem` object store, `schema_config` set for v13, and `limits_config.retention_period: 168h` (7 days). See [monitoring/loki/config.yml](monitoring/loki/config.yml).
- Promtail: uses `docker_sd_configs` to discover containers via the Docker socket, relabels `__meta_docker_container_name` -> `container` and uses container labels (e.g. `app`) to filter which logs to ship. See [monitoring/promtail/config.yml](monitoring/promtail/config.yml).
- Docker Compose mounts:
	- Promtail needs `/var/run/docker.sock:ro` and `/var/lib/docker/containers:ro` to read logs.
	- Named volumes `loki-data` and `grafana-data` persist data between restarts.

Config snippets
---
Loki client and retention snippet (from `monitoring/loki/config.yml`):

```yaml
limits_config:
	retention_period: 168h
storage_config:
	tsdb:
		dir: /loki/tsdb
		index_type: tsdb
		filesystem:
			directory: /loki/chunks
```

Promtail client and docker discovery (from `monitoring/promtail/config.yml`):

```yaml
clients:
	- url: http://loki:3100/loki/api/v1/push

scrape_configs:
	- job_name: docker
		docker_sd_configs:
			- host: unix:///var/run/docker.sock
				refresh_interval: 5s
		relabel_configs:
			- source_labels: [__meta_docker_container_name]
				target_label: container
				regex: \/?(.*)
```

Application structured logging (Python)
--
The Python app was updated to emit JSON logs. Example formatter using `python-json-logger`:

```python
from pythonjsonlogger import jsonlogger
import logging

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger.info('App startup', extra={'module': 'app', 'port': 8000})
```

Log labels
--
Promtail relabeling ensures each log stream contains labels like `app` and `container`. Use these in queries for efficient selection.

LogQL examples used in Grafana
--
- Show all python app logs:
	{app="devops-python"}
- Only ERROR lines:
	{app="devops-python"} |= "ERROR"
- Parse JSON and filter by HTTP method:
	{app="devops-python"} | json | method="GET"
- Logs per second by app (time series):
	sum by (app) (rate({app=~"devops-.*"}[1m]))

Dashboard (panels)
---
I created a Grafana dashboard with four panels:
1. Logs Table — Query: `{app=~"devops-.*"}` (shows recent logs)
2. Request Rate — Query: `sum by (app) (rate({app=~"devops-.*"} [1m]))` (time series)
3. Error Logs — Query: `{app=~"devops-.*"} | json | level="ERROR"` (filtered logs)
4. Log Level Distribution — Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

Production-readiness changes
---
- Resource limits :

```yaml
    mem_limit: 128m
    cpus: 0.20
```

- Secure Grafana: disable anonymous access (`GF_AUTH_ANONYMOUS_ENABLED=false`) and set admin credentials via env or `.env` file.
- Healthchecks added for Loki and Grafana (see `docker-compose.yml`).

Screenshots (evidence)
----
All collected screenshots are included below (embedded from `monitoring/docs/screenshots/`).

- Compose services up and healthy:

![Compose ps](/monitoring/docs/screenshots/compose_ps.png)

- Docker processes after healthchecks:

![Docker ps healthchecks](/monitoring/docs/screenshots/docker_ps_after_healthchecks.png)

- Grafana login page (secured, no anonymous access):

![Grafana login](/monitoring/docs/screenshots/grafana_login_page.png)

- Grafana overview / home:

![Grafana UI](/monitoring/docs/screenshots/grafana.png)

- Grafana Explore: Loki data source (Loki selected):

![Grafana Explore Loki](/monitoring/docs/screenshots/grafana_explore_loki.png)

- Grafana Explore: Promtail logs / targets view:

![Promtail Explore](/monitoring/docs/screenshots/grafana_explore_promtail.png)

- Grafana Explore: Grafana-specific Explore screenshot showing app streams:

![Grafana Explore Grafana](/monitoring/docs/screenshots/grafana_explore_grafana.png)

- Python app raw logs (JSON lines):

![App Python Logs](/monitoring/docs/screenshots/app_python_logs.png)

- Python app parsed JSON fields (parsed view):

![App Python Parsed](/monitoring/docs/screenshots/app_python_parsed.png)

- Python app error lines captured in Loki:

![App Python Errors](/monitoring/docs/screenshots/app_python_errors.png)

Notes: all screenshots are stored in [monitoring/docs/screenshots](monitoring/docs/screenshots).

Challenges and notes
---
- Promtail requires access to the Docker socket and container logs; this is a known security tradeoff. For production, use a dedicated log-shipping sidecar or run promtail on dedicated logging hosts.
- Ensuring correct relabeling was the main troubleshooting step — verifying `__meta_docker_container_name` and container labels in Promtail targets helped narrow the streams.
