package main

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/gorilla/websocket"
)

func TestServerHealthEndpoint(t *testing.T) {
	router := SetupServerRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/health", nil)
	req.Header.Set("X-Trace-ID", "test-trace-123")

	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
	if w.Header().Get("X-Trace-ID") != "test-trace-123" {
		t.Fatalf("expected trace-id header test-trace-123, got %s", w.Header().Get("X-Trace-ID"))
	}
}

func TestServerProcessEndpoint(t *testing.T) {
	router := SetupServerRouter()
	w := httptest.NewRecorder()
	body := []byte(`{"action":"sync","items":5}`)
	req, _ := http.NewRequest("POST", "/api/v1/process", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
}

func TestServerWebSocketEndpoint(t *testing.T) {
	router := SetupServerRouter()
	server := httptest.NewServer(router)
	defer server.Close()

	u, _ := url.Parse(server.URL)
	u.Scheme = "ws"
	u.Path = "/ws"

	header := http.Header{}
	header.Set("X-Trace-ID", "ws-trace-456")

	ws, _, err := websocket.DefaultDialer.Dial(u.String(), header)
	if err != nil {
		t.Fatalf("ws connection failed: %v", err)
	}
	defer ws.Close()

	var msg map[string]interface{}
	if err := ws.ReadJSON(&msg); err != nil {
		t.Fatalf("failed to read initial message: %v", err)
	}
	if msg["trace_id"] != "ws-trace-456" {
		t.Errorf("expected trace_id ws-trace-456, got %v", msg["trace_id"])
	}

	if err := ws.WriteMessage(websocket.TextMessage, []byte("ping")); err != nil {
		t.Fatalf("failed to send message: %v", err)
	}

	var echoMsg map[string]interface{}
	if err := ws.ReadJSON(&echoMsg); err != nil {
		t.Fatalf("failed to read echo message: %v", err)
	}
	if echoMsg["echo"] != "ping" {
		t.Errorf("expected echo 'ping', got %v", echoMsg["echo"])
	}
}
