# DevOps Info Service

## Overview
DevOps Info Service is a simple Python web application built with Flask. It provides information about the system it is running on and its own health status.

## Prerequisites
- Python 3.11+ is required.
- `pip` (Python package installer)

## Installation
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
To run the application with default settings:
```bash
python app.py
```
The app will be available at `http://localhost:8080`.

To run with custom configuration:
```bash
PORT=8080 python app.py
```

## API Endpoints

### `GET /`
Returns comprehensive Service and System information.

**Response Schema:**
```json
{
  "service": {
    "name": "str",
    "version": "str",
    "description": "str",
    "framework": "str"
  },
  "system": {
    "hostname": "str",
    "platform": "str",
    "platform_version": "str",
    "architecture": "str",
    "cpu_count": "int",
    "python_version": "str"
  },
  "runtime": {
    "uptime_seconds": "int",
    "uptime_human": "str",
    "current_time": "ISO8601 str",
    "timezone": "str"
  },
  "request": {
    "client_ip": "str",
    "user_agent": "str",
    "method": "str",
    "path": "str"
  },
  "endpoints": [
    {"path": "str", "method": "str", "description": "str"}
  ]
}
```

**Example Request:**
```bash
curl http://localhost:8080/
```

### `GET /health`
Returns a simple health check status.

**Response Schema:**
```json
{
  "status": "str",
  "timestamp": "ISO8601 str",
  "uptime_seconds": "int"
}
```

**Example Request:**
```bash
curl http://localhost:8080/health
```

## Configuration
The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST`   | Host to bind to | `0.0.0.0` |
| `PORT`   | Port to listen on | `8080` |
| `DEBUG`  | Enable debug mode | `False` |
