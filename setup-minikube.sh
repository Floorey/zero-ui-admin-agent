#!/usr/bin/env bash
set -e

echo "================================================================="
echo "   STARTING MINIKUBE CLUSTER & DEPLOYING ZERO-TRUST AGENT STACK   "
echo "================================================================="

# 1. Start Minikube Cluster
if ! minikube status >/dev/null 2>&1; then
    echo "[+] Starting Minikube cluster..."
    minikube start --driver=docker --cpus=2 --memory=4096
else
    echo "[✔] Minikube cluster is already running."
fi

# 2. Point local terminal shell to Minikube's Docker daemon
echo "[+] Configuring shell for Minikube Docker environment..."
eval $(minikube -p minikube docker-env)

# 3. Build local Docker container images inside Minikube
echo "[+] Building container images inside Minikube..."
docker build -t k8s-backend-server:latest -f server/Dockerfile .
docker build -t k8s-zero-trust-proxy:latest -f proxy/Dockerfile .

# 4. Apply Kubernetes Manifests
echo "[+] Deploying Kubernetes manifests to 'zero-trust-agent' namespace..."
kubectl apply -f k8s/cluster-manifests.yaml

# 5. Output Cluster Status
echo "================================================================="
echo "[✔] Deployment Complete! Active Pods:"
kubectl get pods -n zero-trust-agent
echo ""
echo "To access the Zero-Trust Proxy via Minikube:"
echo "minikube service proxy-middleware -n zero-trust-agent --url"
echo "================================================================="
