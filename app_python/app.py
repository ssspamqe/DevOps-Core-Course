"""
DevOps Info Service
Flask app with structured JSON logging
Includes Promtail labels for log filtering
"""

import os
import sys
import socket
import platform
import logging
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------

class RequestContextFilter(logging.Filter):
    """Inject request context and Promtail labels into log records."""

    PROMTAIL_LABELS = {
        "logging": "promtail",
        "app": "devops-info-service"  # change if your app name differs
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

        # Inject Promtail labels
        for k, v in self.PROMTAIL_LABELS.items():
            setattr(record, k, v)

        return True

def setup_logging():
    """Configure structured JSON logging with Promtail labels."""
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

    # Make Flask/Werkzeug logs structured
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
# Request Logging
# ------------------------------------------------------------------------------

@app.before_request
def before_request():
    g.request_start = datetime.now(timezone.utc)
    g.request_id = str(uuid.uuid4())
    logger.info("request_start", extra={"request_id": g.request_id})

@app.after_request
def after_request(response):
    duration_ms = None
    try:
        duration_ms = int(
            (datetime.now(timezone.utc) - g.request_start).total_seconds() * 1000
        )
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
def index():
    """Main endpoint - service and system information."""
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
            {"path": "/health", "method": "GET", "description": "Health check"}
        ]
    }

    logger.info("main_endpoint_called", extra={"request_id": g.request_id})
    return jsonify(response_data)

@app.route("/health")
def health():
    """Health check endpoint."""
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - START_TIME).total_seconds())
    response_data = {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "uptime_seconds": uptime_seconds
    }
    logger.info("health_check", extra={"request_id": g.request_id})
    return jsonify(response_data)

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