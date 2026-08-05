package main

import (
	"crypto/rand"
	"encoding/hex"
	"log"
	"net/http/httputil"
	"net/url"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

func TraceAndAuditMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		traceID := c.GetHeader("X-Trace-ID")
		if traceID == "" {
			b := make([]byte, 16)
			rand.Read(b)
			traceID = hex.EncodeToString(b)
		}
		c.Set("TraceID", traceID)
		c.Header("X-Trace-ID", traceID)
		c.Request.Header.Set("X-Trace-ID", traceID)

		c.Next()

		log.Printf("[MW-TRACE] trace_id=%s method=%s path=%s status=%d latency=%v",
			traceID, c.Request.Method, c.Request.URL.Path, c.Writer.Status(), time.Since(start))
	}
}

func ReverseProxyHandler(targetURL string) gin.HandlerFunc {
	target, err := url.Parse(targetURL)
	if err != nil {
		log.Fatalf("invalid target url: %v", err)
	}
	proxy := httputil.NewSingleHostReverseProxy(target)

	return func(c *gin.Context) {
		c.Request.Host = target.Host
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}

func SetupMiddlewareRouter(targetServer string) *gin.Engine {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery(), TraceAndAuditMiddleware())

	r.Any("/*proxyPath", ReverseProxyHandler(targetServer))

	return r
}

func main() {
	targetServer := os.Getenv("SERVER_POD_URL")
	if targetServer == "" {
		targetServer = os.Getenv("BACKEND_SERVER_URL")
		if targetServer == "" {
			targetServer = "http://localhost:8080"
		}
	}
	r := SetupMiddlewareRouter(targetServer)
	port := os.Getenv("MIDDLEWARE_PORT")
	if port == "" {
		port = os.Getenv("PROXY_PORT")
		if port == "" {
			port = "8443"
		}
	}
	_ = r.Run(":" + port)
}
