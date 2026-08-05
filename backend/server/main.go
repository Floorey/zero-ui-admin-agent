package main

import (
	"crypto/rand"
	"encoding/hex"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

func TraceMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		traceID := c.GetHeader("X-Trace-ID")
		if traceID == "" {
			b := make([]byte, 16)
			rand.Read(b)
			traceID = hex.EncodeToString(b)
		}
		c.Set("TraceID", traceID)
		c.Header("X-Trace-ID", traceID)
		c.Next()
	}
}

func SetupServerRouter() *gin.Engine {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery(), TraceMiddleware())

	api := r.Group("/api/v1")
	{
		api.GET("/health", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{
				"status":    "UP",
				"service":   "server-pod-1",
				"trace_id":  c.GetString("TraceID"),
				"timestamp": time.Now().UTC(),
			})
		})

		api.POST("/process", func(c *gin.Context) {
			var body map[string]interface{}
			if err := c.ShouldBindJSON(&body); err != nil {
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error(), "trace_id": c.GetString("TraceID")})
				return
			}
			c.JSON(http.StatusOK, gin.H{
				"status":   "processed",
				"payload":  body,
				"trace_id": c.GetString("TraceID"),
			})
		})
	}

	r.GET("/ws", func(c *gin.Context) {
		conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			return
		}
		defer conn.Close()

		traceID := c.GetString("TraceID")
		_ = conn.WriteJSON(gin.H{"type": "connected", "trace_id": traceID})

		for {
			mt, message, err := conn.ReadMessage()
			if err != nil {
				break
			}
			response := gin.H{
				"echo":     string(message),
				"trace_id": traceID,
				"time":     time.Now().UTC(),
			}
			if err := conn.WriteJSON(response); err != nil {
				_ = mt
				break
			}
		}
	})

	return r
}

func main() {
	r := SetupServerRouter()
	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8080"
	}
	_ = r.Run(":" + port)
}
