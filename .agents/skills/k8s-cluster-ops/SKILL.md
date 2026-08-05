---
name: k8s-cluster-ops
description: "Instructions and standards for managing Kubernetes cluster topology, pod mesh health, namespace isolation, and deployment strategies."
---

# Kubernetes Cluster Operations Skill

This skill provides guidelines and operational procedures for managing Kubernetes clusters within the multi-agent system.

## Core Directives
1. **Namespace Isolation**: `ingress-system`, `agent-system`, `default`, `database`.
2. **Pod Health Monitoring**: Probe requirements and restart thresholds.
3. **Deployment Strategy**: Rolling update strategy with `maxSurge: 25%`.
