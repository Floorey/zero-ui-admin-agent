# Multi-stage CGO_ENABLED=0 pure Go build
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/proxy_server ./backend/middleware

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/proxy_server ./proxy
EXPOSE 8443
ENTRYPOINT ["./proxy"]
