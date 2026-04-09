"""
DevOps Info Service
Flask app with structured JSON logging and Prometheus metrics
"""

import os
import sys
import socket
import platform
import logging
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g, Response
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------

class RequestContextFilter(logging.Filter):
    PROMTAIL_LABELS = {
        "logging": "promtail",
        "app": "devops-info-service"
    }

    def filter(self, record):
        try:
            record.client_ip = request.remote_addr
            record.method = request.method
            record.path = request.path
            record.user_agent = request.headers.get("User-Agent")
            record.query = request.query_string.decode("utf-8")
            record.request_id = getattr(g, "request_id", None)
        except RuntimeError:
            record.client_ip = None
            record.method = None
            record.path = None
            record.user_agent = None
            record.query = None
            record.request_id = None

        for k, v in self.PROMTAIL_LABELS.items():
            setattr(record, k, v)
        return True

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(client_ip)s %(method)s %(path)s %(query)s %(user_agent)s "
        "%(status)s %(duration_ms)s %(request_id)s "
        "%(logging)s %(app)s",
        timestamp=True
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.setLevel(logging.INFO)

setup_logging()
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# App Setup
# ------------------------------------------------------------------------------

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)

# ------------------------------------------------------------------------------
# Metrics Setup
# ------------------------------------------------------------------------------

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

endpoint_calls = Counter(
    'devops_info_endpoint_calls', 
    'Endpoint calls', 
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds', 
    'System info collection time'
)

# ------------------------------------------------------------------------------
# Request Handling
# ------------------------------------------------------------------------------

@app.before_request
def before_request():
    http_requests_in_progress.inc()
    g.request_start = datetime.now(timezone.utc)
    g.request_id = str(uuid.uuid4())
    logger.info("request_start", extra={"request_id": g.request_id})

@app.after_request
def after_request(response):
    http_requests_in_progress.dec()
    duration_ms = None
    try:
        duration_s = (datetime.now(timezone.utc) - g.request_start).total_seconds()
        duration_ms = int(duration_s * 1000)
        
        endpoint = request.url_rule.rule if request.url_rule else request.path

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration_s)
    except Exception:
        pass
    logger.info(
        "request_end",
        extra={
            "status": response.status_code,
            "duration_ms": duration_ms,
            "request_id": getattr(g, "request_id", None)
        }
    )
    return response

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@app.route("/")
@system_info_duration.time()
def index():
    endpoint_calls.labels(endpoint='/').inc()
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - START_TIME).total_seconds())
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60

    response_data = {
        "service": {
            "name": "devops-info-service",
            "version": os.getenv("VERSION", "1.0.0"),
            "description": "DevOps course info service",
            "framework": "Flask"
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        },
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": f"{hours} hour, {minutes} minutes",
            "current_time": now.isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
            "query": request.query_string.decode("utf-8")
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
        ]
    }

    logger.info("main_endpoint_called", extra={"request_id": g.request_id})
    return jsonify(response_data)

@app.route("/health")
def health():
    endpoint_calls.labels(endpoint='/health').inc()
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - START_TIME).total_seconds())
    response_data = {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "uptime_seconds": uptime_seconds
    }
    logger.info("health_check", extra={"request_id": g.request_id})
    return jsonify(response_data)

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ------------------------------------------------------------------------------
# Error Handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def handle_404(error):
    logger.warning("endpoint_not_found", extra={"request_id": getattr(g, "request_id", None)})
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

@app.errorhandler(500)
def handle_500(error):
    logger.exception("internal_server_error", extra={"request_id": getattr(g, "request_id", None)})
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

@app.errorhandler(Exception)
def handle_unhandled_exception(error):
    logger.exception("unhandled_exception", extra={"request_id": getattr(g, "request_id", None)})
    return jsonify({"error": "Internal Server Error"}), 500

# ------------------------------------------------------------------------------
# Application Entry
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(
        "app_startup",
        extra={
            "host": host,
            "port": port,
            "debug": debug_mode,
            "version": os.getenv("VERSION", "1.0.0")
        }
    )

    app.run(host=host, port=port, debug=debug_mode)
