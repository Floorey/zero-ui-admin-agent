# Windows 11 PowerShell Initialization Script for Zero-Trust Agent Cluster
Write-Host "Starting Zero-Trust Agent Cluster Initialization..." -ForegroundColor Cyan

if (Get-Command python -ErrorAction SilentlyContinue) {
    python start.py
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 start.py
} else {
    Write-Host "Python not found in PATH. Launching via Docker Compose directly..." -ForegroundColor Yellow
    docker compose up -d
}
