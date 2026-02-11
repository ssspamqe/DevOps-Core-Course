# DevOps Info Service

[![Python Application CI/CD](https://github.com/ssspamqe/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/ssspamqe/DevOps-Core-Course/actions/workflows/python-ci.yml)

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

## Running Tests
To run the automated tests with code coverage:

1. Install test dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests with coverage report:
   ```bash
   pytest --cov=. tests/
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

## Docker

You can also run this application as a Docker container.

### 1. Build the Image
To build the Docker image locally, run:
```bash
docker build -t <image_name> .
```

### 2. Run the Container
To run the container and map the ports:
```bash
docker run -p <host_port>:8080 <image_name>
```

### 3. Pull from Docker Hub
To pull the pre-built image from Docker Hub:
```bash
docker pull ssspamqe/lab2_app_python:ssspamqe
```
