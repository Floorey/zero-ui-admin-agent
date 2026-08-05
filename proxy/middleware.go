package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

type ConcurrencyGovernor struct {
	sem chan struct{}
}

func NewConcurrencyGovernor(maxConcurrent int) *ConcurrencyGovernor {
	return &ConcurrencyGovernor{sem: make(chan struct{}, maxConcurrent)}
}

func (cg *ConcurrencyGovernor) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		select {
		case cg.sem <- struct{}{}:
			defer func() { <-cg.sem }()
			c.Next()
		default:
			c.AbortWithStatusJSON(http.StatusServiceUnavailable, gin.H{
				"error":    "load_shedding",
				"message":  "Server load shed: capacity exceeded",
				"trace_id": c.GetString("TraceID"),
			})
		}
	}
}

func generateTraceID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(b)
}

func TraceAndAuditLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		traceID := c.GetHeader("X-Trace-ID")
		if traceID == "" {
			traceID = generateTraceID()
		}
		c.Set("TraceID", traceID)
		c.Header("X-Trace-ID", traceID)
		c.Next()
		log.Printf("[AUDIT] trace_id=%s method=%s path=%s status=%d ip=%s latency=%v",
			traceID, c.Request.Method, c.Request.URL.Path, c.Writer.Status(), c.ClientIP(), time.Since(start))
	}
}

func ZeroTrustAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.GetHeader("Authorization") == "" && c.GetHeader("X-Client-Cert-SHA256") == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"error":    "zero_trust_violation",
				"message":  "Missing valid client identity token",
				"trace_id": c.GetString("TraceID"),
			})
			return
		}
		c.Header("X-Zero-Trust-Validated", "true")
		c.Next()
	}
}

func NewReverseProxy(targetURL string) gin.HandlerFunc {
	target, err := url.Parse(targetURL)
	if err != nil {
		log.Fatalf("Invalid backend URL: %v", err)
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	return func(c *gin.Context) {
		c.Request.Host = target.Host
		c.Request.Header.Set("X-Forwarded-Host", c.Request.Header.Get("Host"))
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	maxReqs := 100
	if envMax := os.Getenv("MAX_CONCURRENT_REQUESTS"); envMax != "" {
		if v, err := strconv.Atoi(envMax); err == nil {
			maxReqs = v
		}
	}
	backendURL := os.Getenv("BACKEND_SERVER_URL")
	if backendURL == "" {
		backendURL = "http://backend-server:8080"
	}

	governor := NewConcurrencyGovernor(maxReqs)
	r.Use(TraceAndAuditLogger())
	r.Use(governor.Middleware())
	r.Use(ZeroTrustAuth())
	r.Any("/*proxyPath", NewReverseProxy(backendURL))

	port := os.Getenv("PROXY_PORT")
	if port == "" {
		port = "8443"
	}
	log.Printf("[PROXY] Zero-Trust Proxy on :%s -> %s (LoadShedCap: %d)", port, backendURL, maxReqs)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Proxy runtime error: %v", err)
	}
}
