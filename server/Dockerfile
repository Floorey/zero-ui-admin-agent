# Multi-stage CGO_ENABLED=0 pure Go build
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/server_bin ./backend/server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/server_bin ./server
COPY static ./static
COPY content ./content
EXPOSE 8080
ENTRYPOINT ["./server"]
