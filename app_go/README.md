# DevOps Info Service (Go Version)

## Overview
This is a Go implementation of the DevOps Info Service. It mirrors the functionality of the Python version, providing system information and health status.

## Prerequisites
- Go 1.21 or higher

## Build and Run

1. **Build the application:**
   ```bash
   go build -o app
   ```

2. **Run the application:**
   ```bash
   ./app
   ```
   The app will typically be available at `http://localhost:8080` (default).

## Configuration
The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST`   | Host to bind to | `0.0.0.0` |
| `PORT`   | Port to listen on | `8080` |

### Example with custom port:
```bash
PORT=9090 ./app
```

## API Endpoints

### `GET /`
Returns comprehensive Service and System information.

**Example Request:**
```bash
curl http://localhost:8080/
```

### `GET /health`
Returns a simple health check status.

**Example Request:**
```bash
curl http://localhost:8080/health
```
