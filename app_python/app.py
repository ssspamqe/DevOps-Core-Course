"""
DevOps Info Service
Main application module
"""
from flask import Flask, jsonify, request
import platform
import socket
import os
import logging
from datetime import datetime, timezone

# Setting up the app
app = Flask(__name__)

# Basic Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Record start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

@app.route('/')
def index():
    """Main endpoint - service and system information."""
    # Calculate uptime
    now = datetime.now(timezone.utc)
    uptime_delta = now - START_TIME
    uptime_seconds = int(uptime_delta.total_seconds())
    
    # Calculate human readable uptime
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    uptime_human = f"{hours} hour, {minutes} minutes"

    # Construct the response data
    response_data = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
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
            "uptime_human": uptime_human,
            "current_time": now.isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"}
        ]
    }
    
    logger.info(f"Main endpoint accessed by {request.remote_addr}")
    return jsonify(response_data)

@app.route('/health')
def health():
    """Health check endpoint."""
    now = datetime.now(timezone.utc)
    uptime_delta = now - START_TIME
    
    response_data = {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "uptime_seconds": int(uptime_delta.total_seconds())
    }
    
    logger.debug("Health check performed")
    return jsonify(response_data)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    # Configuration from environment variables
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Server starting on {host}:{port}")
    app.run(host=host, port=port, debug=debug_mode)
