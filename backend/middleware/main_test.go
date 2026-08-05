package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

type CloseNotifyingRecorder struct {
	*httptest.ResponseRecorder
	closed chan bool
}

func (c *CloseNotifyingRecorder) CloseNotify() <-chan bool {
	return c.closed
}

func newCloseNotifyingRecorder() *CloseNotifyingRecorder {
	return &CloseNotifyingRecorder{
		ResponseRecorder: httptest.NewRecorder(),
		closed:           make(chan bool, 1),
	}
}

func TestMiddlewareTraceAndProxy(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		traceID := r.Header.Get("X-Trace-ID")
		if traceID == "" {
			t.Errorf("expected X-Trace-ID header in proxied request")
		}
		w.Header().Set("X-Trace-ID", traceID)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"proxied"}`))
	}))
	defer mockServer.Close()

	mwRouter := SetupMiddlewareRouter(mockServer.URL)

	w := newCloseNotifyingRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/health", nil)

	mwRouter.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
	if w.Header().Get("X-Trace-ID") == "" {
		t.Fatalf("expected X-Trace-ID header in response")
	}
}

func TestMiddlewarePreservesExistingTraceID(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Trace-ID", r.Header.Get("X-Trace-ID"))
		w.WriteHeader(http.StatusOK)
	}))
	defer mockServer.Close()

	mwRouter := SetupMiddlewareRouter(mockServer.URL)

	w := newCloseNotifyingRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/data", nil)
	req.Header.Set("X-Trace-ID", "custom-trace-uuid-999")

	mwRouter.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
	if w.Header().Get("X-Trace-ID") != "custom-trace-uuid-999" {
		t.Fatalf("expected preserved trace ID custom-trace-uuid-999, got %s", w.Header().Get("X-Trace-ID"))
	}
}
