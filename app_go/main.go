package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"
)

var startTime time.Time

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

	// Configure logging
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	// Routes
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/health", handleHealth)

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Server starting on %s", addr)

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}

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
			PlatformVersion: "N/A", // Not easily available in stdlib
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
		},
		Endpoints: []Endpoint{
			{"/", "GET", "Service information"},
			{"/health", "GET", "Health check"},
		},
	}

	log.Printf("Main endpoint accessed by %s", clientIP)
	writeJSON(w, resp)
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	now := time.Now().UTC()
	uptime := now.Sub(startTime)

	resp := HealthResponse{
		Status:        "healthy",
		Timestamp:     now.Format(time.RFC3339),
		UptimeSeconds: int64(uptime.Seconds()),
	}

	log.Println("Health check performed")
	writeJSON(w, resp)
}

func handleNotFound(w http.ResponseWriter, r *http.Request) {
	resp := ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	}
	w.WriteHeader(http.StatusNotFound)
	writeJSON(w, resp)
}

func writeJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(data); err != nil {
		log.Printf("Error encoding response: %v", err)
	}
}
