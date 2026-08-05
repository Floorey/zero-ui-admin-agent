# Makefile for cross-platform Agent Kit startup

# Variables
DOCKER_COMPOSE = docker compose
GO_RUN = go run

.PHONY: all up down logs run-local

# Default target
all: up

# Start the entire stack (Postgres, Proxies, Genkit)
up:
	@echo "Starting the Zero-Trust Agent Cluster..."
	$(DOCKER_COMPOSE) up -d

# Stop the stack
down:
	@echo "Shutting down the cluster..."
	$(DOCKER_COMPOSE) down

# View logs for the AI engine
logs:
	$(DOCKER_COMPOSE) logs -f my-genkit-gin

# Run the Go Genkit Agent locally (outside Docker for quick debugging)
# This will work flawlessly on Windows, WSL, and Linux as long as Go is installed
run-local:
	@echo "Starting Agent locally on port 8081..."
	cd my-genkit-gin && export GEMINI_API_KEY=$(GEMINI_API_KEY) && $(GO_RUN) .
