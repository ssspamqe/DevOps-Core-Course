package main

import (
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"

	"github.com/gofrs/uuid"
)

var startTime time.Time

type LogEntry struct {
	Timestamp  string `json:"timestamp"`
	Level      string `json:"level"`
	Message    string `json:"message"`
	ClientIP   string `json:"client_ip,omitempty"`
	Method     string `json:"method,omitempty"`
	Path       string `json:"path,omitempty"`
	Query      string `json:"query,omitempty"`
	UserAgent  string `json:"user_agent,omitempty"`
	Status     int    `json:"status,omitempty"`
	DurationMS int64  `json:"duration_ms,omitempty"`
	RequestID  string `json:"request_id,omitempty"`
	Logging    string `json:"logging"`
	App        string `json:"app"`
	Stack      string `json:"stack,omitempty"`
}

type ServiceInfo struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
	Query     string `json:"query,omitempty"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ResponseData struct {
	Service   ServiceInfo `json:"service"`
	System    SystemInfo  `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

func main() {
	startTime = time.Now().UTC()

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	addr := fmt.Sprintf("%s:%s", host, port)

	http.HandleFunc("/", loggingMiddleware(handleIndex))
	http.HandleFunc("/health", loggingMiddleware(handleHealth))

	logJSON("INFO", "server_starting", nil)

	if err := http.ListenAndServe(addr, nil); err != nil {
		logJSON("FATAL", "server_failed", map[string]interface{}{"error": err.Error()})
	}
}

// ---------------- Logging ----------------

func generateUUID() string {
	raw, _ := uuid.NewV4()
	return raw.String()
}

func logJSON(level string, message string, extra map[string]interface{}) {
	entry := LogEntry{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Level:     level,
		Message:   message,
		Logging:   "promtail",
		App:       "devops-info-service",
	}

	if extra != nil {
		if v, ok := extra["client_ip"].(string); ok {
			entry.ClientIP = v
		}
		if v, ok := extra["method"].(string); ok {
			entry.Method = v
		}
		if v, ok := extra["path"].(string); ok {
			entry.Path = v
		}
		if v, ok := extra["query"].(string); ok {
			entry.Query = v
		}
		if v, ok := extra["user_agent"].(string); ok {
			entry.UserAgent = v
		}
		if v, ok := extra["status"].(int); ok {
			entry.Status = v
		}
		if v, ok := extra["duration_ms"].(int64); ok {
			entry.DurationMS = v
		}
		if v, ok := extra["request_id"].(string); ok {
			entry.RequestID = v
		}
		if v, ok := extra["stack"].(string); ok {
			entry.Stack = v
		}
	}

	data, _ := json.Marshal(entry)
	fmt.Println(string(data))
}

// ---------------- Middleware ----------------

func loggingMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		requestID := generateUUID()

		// Store request ID in context for downstream logging
		r.Header.Set("X-Request-ID", requestID)

		// Call handler
		next(w, r)

		duration := time.Since(start).Milliseconds()
		clientIP, _, err := net.SplitHostPort(r.RemoteAddr)
		if err != nil {
			clientIP = r.RemoteAddr
		}

		logJSON("INFO", "request_end", map[string]interface{}{
			"client_ip":   clientIP,
			"method":      r.Method,
			"path":        r.URL.Path,
			"query":       r.URL.RawQuery,
			"user_agent":  r.UserAgent(),
			"duration_ms": duration,
			"request_id":  requestID,
		})
	}
}

// ---------------- Handlers ----------------

func handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		handleNotFound(w, r)
		return
	}

	now := time.Now().UTC()
	uptime := now.Sub(startTime)
	uptimeSeconds := int64(uptime.Seconds())
	hours := int64(uptime.Hours())
	minutes := int64(uptime.Minutes()) % 60
	uptimeHuman := fmt.Sprintf("%d hour, %d minutes", hours, minutes)

	hostname, _ := os.Hostname()
	clientIP, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		clientIP = r.RemoteAddr
	}
	requestID := r.Header.Get("X-Request-ID")

	resp := ResponseData{
		Service: ServiceInfo{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: SystemInfo{
			Hostname:        hostname,
			Platform:        runtime.GOOS,
			PlatformVersion: "N/A",
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   now.Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  clientIP,
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
			Query:     r.URL.RawQuery,
		},
		Endpoints: []Endpoint{
			{"/", "GET", "Service information"},
			{"/health", "GET", "Health check"},
		},
	}

	logJSON("INFO", "main_endpoint_called", map[string]interface{}{
		"client_ip":  clientIP,
		"method":     r.Method,
		"path":       r.URL.Path,
		"user_agent": r.UserAgent(),
		"request_id": requestID,
	})

	writeJSON(w, resp)
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	now := time.Now().UTC()
	uptime := now.Sub(startTime)

	requestID := r.Header.Get("X-Request-ID")

	resp := HealthResponse{
		Status:        "healthy",
		Timestamp:     now.Format(time.RFC3339),
		UptimeSeconds: int64(uptime.Seconds()),
	}

	logJSON("INFO", "health_check", map[string]interface{}{
		"request_id": requestID,
	})

	writeJSON(w, resp)
}

func handleNotFound(w http.ResponseWriter, r *http.Request) {
	requestID := r.Header.Get("X-Request-ID")
	resp := ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	}
	w.WriteHeader(http.StatusNotFound)
	logJSON("WARN", "endpoint_not_found", map[string]interface{}{
		"path":       r.URL.Path,
		"method":     r.Method,
		"request_id": requestID,
	})
	writeJSON(w, resp)
}

func writeJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(data); err != nil {
		logJSON("ERROR", "error_encoding_response", map[string]interface{}{"error": err.Error()})
	}
}
