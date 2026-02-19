# Lab 1 - Go Implementation Details

## 1. Implementation Overview
The Go application replicates the functionality of the Python Flask app using the standard `net/http` library.

### Key Components:
- **`main.go`**: Contains the server setup, route handlers, and struct definitions.
- **`structs`**: Defined `ServiceInfo`, `SystemInfo`, etc., to enforce the JSON structure.
- **`json` tags**: Used to map struct fields to specific JSON keys (e.g., `uptime_seconds`).

## 2. JSON Structure Matching
I ensured the JSON output matches the Python version by defining Go structs with `json:"key_name"` tags.

One minor adaptation:
- `python_version` key was replaced with `go_version` to reflect the runtime environment.

## 3. Best Practices
- **Standard Library**: Used `net/http` to avoid external dependencies.
- **Environment Variables**: `os.Getenv` is used for configuration.
- **Logging**: `log` package used for server logs.
- **Error Handling**: Checks for errors during JSON encoding and server startup.

## 4. Testing Evidence

### Compilation
*(Screenshot of `go build` command)* Note: Place screenshot in `docs/screenshots/build.png`

### Running the App
*(Screenshot of `./app` running)* Note: Place screenshot in `docs/screenshots/run.png`

### Main Endpoint (`/`)
*(Screenshot of `curl localhost:8080/`)* Note: Place screenshot in `docs/screenshots/endpoint_main.png`

### Health Check (`/health`)
*(Screenshot of `curl localhost:8080/health`)* Note: Place screenshot in `docs/screenshots/endpoint_health.png`
