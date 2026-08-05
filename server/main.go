package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	_ "github.com/lib/pq"
)

type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
	TraceID   string    `json:"trace_id,omitempty"`
	Database  string    `json:"database"`
}

type DataPayload struct {
	ID        int       `json:"id"`
	Key       string    `json:"key"`
	Value     string    `json:"value"`
	CreatedAt time.Time `json:"created_at"`
}

type Server struct {
	db         *sql.DB
	staticDir  string
	contentDir string
}

func (s *Server) zeroTrustValidation(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		traceID := r.Header.Get("X-Trace-ID")
		w.Header().Set("X-Trace-ID", traceID)
		next(w, r)
	}
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	dbStatus := "connected"
	if s.db != nil {
		if err := s.db.PingContext(r.Context()); err != nil {
			dbStatus = fmt.Sprintf("unreachable: %v", err)
		}
	} else {
		dbStatus = "unconfigured"
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(HealthResponse{
		Status:    "UP",
		Timestamp: time.Now().UTC(),
		TraceID:   r.Header.Get("X-Trace-ID"),
		Database:  dbStatus,
	})
}

func (s *Server) handleData(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if s.db == nil {
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"message":  "Standalone execution mode (no DB string provided)",
			"trace_id": r.Header.Get("X-Trace-ID"),
			"data": []DataPayload{
				{ID: 1, Key: "ui_theme", Value: "fine_dining_noma_frantzen", CreatedAt: time.Now().UTC()},
			},
		})
		return
	}

	rows, err := s.db.QueryContext(r.Context(), "SELECT id, key, value, created_at FROM app_data LIMIT 50")
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error":    "query_failed",
			"details":  err.Error(),
			"trace_id": r.Header.Get("X-Trace-ID"),
		})
		return
	}
	defer rows.Close()

	var results []DataPayload
	for rows.Next() {
		var item DataPayload
		if err := rows.Scan(&item.ID, &item.Key, &item.Value, &item.CreatedAt); err == nil {
			results = append(results, item)
		}
	}
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":   "success",
		"count":    len(results),
		"data":     results,
		"trace_id": r.Header.Get("X-Trace-ID"),
	})
}

func (s *Server) handleStaticFiles(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/static/")
	if path == "" || r.URL.Path == "/" {
		path = "index.html"
	}
	fullPath := filepath.Join(s.staticDir, filepath.Clean(path))
	if _, err := os.Stat(fullPath); os.IsNotExist(err) {
		fullPath = filepath.Join(s.staticDir, "index.html")
	}
	http.ServeFile(w, r, fullPath)
}

func (s *Server) handleContentFiles(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/content/")
	fullPath := filepath.Join(s.contentDir, filepath.Clean(path))
	if _, err := os.Stat(fullPath); os.IsNotExist(err) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{
			"error":    "content_not_found",
			"message":  "Requested asset/PDF not found in content directory",
			"trace_id": r.Header.Get("X-Trace-ID"),
		})
		return
	}
	http.ServeFile(w, r, fullPath)
}

func initDB() *sql.DB {
	connStr := os.Getenv("POSTGRES_CONN_STRING")
	if connStr == "" {
		log.Println("[SERVER] POSTGRES_CONN_STRING empty")
		return nil
	}
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Printf("[SERVER] DB err: %v", err)
		return nil
	}
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)
	return db
}

func main() {
	staticDir := os.Getenv("STATIC_DIR")
	if staticDir == "" {
		staticDir = "./static"
	}
	contentDir := os.Getenv("CONTENT_DIR")
	if contentDir == "" {
		contentDir = "./content"
	}

	srv := &Server{
		db:         initDB(),
		staticDir:  staticDir,
		contentDir: contentDir,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/api/v1/health", srv.zeroTrustValidation(srv.handleHealth))
	mux.HandleFunc("/api/v1/data", srv.zeroTrustValidation(srv.handleData))
	mux.HandleFunc("/content/", srv.handleContentFiles)
	mux.HandleFunc("/static/", srv.handleStaticFiles)
	mux.HandleFunc("/", srv.handleStaticFiles)

	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8080"
	}
	httpSrv := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("[SERVER] Pure Go Backend & Fine-Dining UI Server listening on :%s", port)
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[SERVER] Listen err: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = httpSrv.Shutdown(ctx)
	log.Println("[SERVER] Stopped")
}
