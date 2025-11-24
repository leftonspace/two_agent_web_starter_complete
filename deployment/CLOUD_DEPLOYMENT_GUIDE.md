# JARVIS Cloud Deployment Guide

Complete guide for deploying JARVIS to cloud platforms with horizontal scaling and auto-scaling.

## Overview

JARVIS supports multiple deployment strategies:
- **Docker Compose**: Multi-container local/VM deployment (3-5 instances)
- **Kubernetes**: Production cloud deployment with auto-scaling (3-50+ instances)
- **Cloud-Specific**: AWS ECS/Fargate, Google Cloud Run, Azure Container Instances

This guide enables:
- **Horizontal Scaling**: Scale from 3 to 50+ instances automatically
- **Auto-Scaling**: CPU/memory-based scaling with HPA
- **Load Balancing**: Nginx/cloud load balancers with health checks
- **High Availability**: Multi-AZ deployment with failover
- **Zero-Downtime Deployments**: Rolling updates with health checks

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Load Balancer                          │
│                (Nginx / Cloud LB / Ingress)                 │
└───────────┬───────────────────┬────────────────┬───────────┘
            │                   │                │
    ┌───────▼────────┐  ┌───────▼────────┐  ┌──▼──────────┐
    │  JARVIS App 1  │  │  JARVIS App 2  │  │  JARVIS App N│
    │   (Pod/Task)   │  │   (Pod/Task)   │  │  (Pod/Task)  │
    └───────┬────────┘  └───────┬────────┘  └──┬───────────┘
            │                   │               │
            └───────────────────┴───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌─────▼──────┐    ┌───────▼──────┐    ┌──────▼──────┐
  │ PostgreSQL │    │    Redis     │    │  Temporal   │
  │  (Primary) │    │ (Message Bus)│    │ (Workflows) │
  └────────────┘    └──────────────┘    └─────────────┘
        │
  ┌─────▼──────┐
  │ PostgreSQL │
  │  (Replica) │
  └────────────┘

     Celery Workers (Auto-Scaled)
  ┌────────┐ ┌────────┐ ┌────────┐
  │Worker 1│ │Worker 2│ │Worker N│
  └────────┘ └────────┘ └────────┘
```

## Quick Start: Docker Compose

### Prerequisites

```bash
# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo apt-get install docker-compose-plugin

# Clone repository
git clone https://github.com/your-org/jarvis.git
cd jarvis
```

### Configuration

Create `.env` file:

```bash
# PostgreSQL
PG_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Custom ports
# POSTGRES_PORT=5432
# REDIS_PORT=6379
```

### Deploy

```bash
# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# Check status
docker-compose -f deployment/docker-compose.yml ps

# View logs
docker-compose -f deployment/docker-compose.yml logs -f jarvis-app-1

# Scale JARVIS instances
docker-compose -f deployment/docker-compose.yml up -d --scale jarvis-app=5

# Scale Celery workers
docker-compose -f deployment/docker-compose.yml up -d --scale celery-worker-model=10
```

### Access

- **JARVIS API**: http://localhost (load balanced)
- **Direct instances**: http://localhost:8001, :8002, :8003
- **Celery Flower**: http://localhost:5555
- **Temporal UI**: http://localhost:8233
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Production: Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install helm (optional)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Configure kubectl for your cluster
# AWS EKS:
aws eks update-kubeconfig --name jarvis-cluster --region us-west-2

# Google GKE:
gcloud container clusters get-credentials jarvis-cluster --zone us-central1-a

# Azure AKS:
az aks get-credentials --resource-group jarvis-rg --name jarvis-cluster
```

### Build and Push Images

```bash
# Build images
docker build -f deployment/Dockerfile.app -t your-registry/jarvis:latest .
docker build -f deployment/Dockerfile.worker -t your-registry/jarvis-worker:latest .

# Push to registry
# Docker Hub:
docker push your-registry/jarvis:latest
docker push your-registry/jarvis-worker:latest

# AWS ECR:
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-west-2.amazonaws.com
docker tag jarvis:latest 123456789.dkr.ecr.us-west-2.amazonaws.com/jarvis:latest
docker push 123456789.dkr.ecr.us-west-2.amazonaws.com/jarvis:latest

# Google GCR:
gcloud auth configure-docker
docker tag jarvis:latest gcr.io/your-project/jarvis:latest
docker push gcr.io/your-project/jarvis:latest
```

### Configure Secrets

```bash
# Create namespace
kubectl create namespace jarvis

# Create secrets
kubectl create secret generic jarvis-secrets \
  --from-literal=pg-password='your_secure_password' \
  --from-literal=redis-password='your_redis_password' \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=anthropic-api-key='sk-ant-...' \
  -n jarvis

# Or from file
kubectl create secret generic jarvis-secrets \
  --from-env-file=.env \
  -n jarvis
```

### Deploy to Kubernetes

```bash
# Apply deployment
kubectl apply -f deployment/kubernetes/jarvis-deployment.yaml

# Check rollout status
kubectl rollout status deployment/jarvis-app -n jarvis

# Check pods
kubectl get pods -n jarvis

# Check HPA (Horizontal Pod Autoscaler)
kubectl get hpa -n jarvis

# View logs
kubectl logs -f deployment/jarvis-app -n jarvis

# Get service endpoint
kubectl get service jarvis-app -n jarvis
```

### Auto-Scaling Configuration

The deployment includes Horizontal Pod Autoscaler (HPA) that automatically scales based on:

**JARVIS App Scaling**:
- **Min replicas**: 3
- **Max replicas**: 20
- **CPU target**: 70%
- **Memory target**: 80%
- **Scale up**: +100% every 15s (max 4 pods)
- **Scale down**: -50% every 60s

**Celery Worker Scaling**:
- **Min replicas**: 5
- **Max replicas**: 30
- **CPU target**: 75%
- **Memory target**: 85%

**Custom metrics** (optional):
```yaml
# Add custom metrics to HPA
metrics:
- type: Pods
  pods:
    metric:
      name: jarvis_request_queue_size
    target:
      type: AverageValue
      averageValue: "100"
```

### Monitoring

```bash
# Watch auto-scaling in real-time
watch kubectl get hpa,pods -n jarvis

# Check resource usage
kubectl top pods -n jarvis
kubectl top nodes

# Check events
kubectl get events -n jarvis --sort-by='.lastTimestamp'

# Install metrics server (if not present)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## Cloud-Specific Deployments

### AWS ECS/Fargate

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name jarvis-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definition.json

# Create service with auto-scaling
aws ecs create-service \
  --cluster jarvis-cluster \
  --service-name jarvis-app \
  --task-definition jarvis:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-123,subnet-456],securityGroups=[sg-789],assignPublicIp=ENABLED}"

# Configure auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/jarvis-cluster/jarvis-app \
  --min-capacity 3 \
  --max-capacity 20

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/jarvis-cluster/jarvis-app \
  --policy-name jarvis-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://deployment/aws/scaling-policy.json
```

### Google Cloud Run

```bash
# Deploy to Cloud Run (auto-scaling built-in)
gcloud run deploy jarvis \
  --image gcr.io/your-project/jarvis:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 3 \
  --max-instances 20 \
  --cpu 2 \
  --memory 4Gi \
  --concurrency 80 \
  --set-env-vars KG_BACKEND=postgres,PG_HOST=<cloud-sql-proxy> \
  --set-secrets PG_PASSWORD=pg-password:latest,OPENAI_API_KEY=openai-key:latest
```

### Azure Container Instances

```bash
# Create resource group
az group create --name jarvis-rg --location eastus

# Deploy container group
az container create \
  --resource-group jarvis-rg \
  --name jarvis-app \
  --image your-registry.azurecr.io/jarvis:latest \
  --cpu 2 \
  --memory 4 \
  --os-type Linux \
  --ip-address Public \
  --ports 8000 \
  --environment-variables \
    KG_BACKEND=postgres \
    PG_HOST=jarvis-postgres.database.azure.com \
  --secure-environment-variables \
    PG_PASSWORD=your_password \
    OPENAI_API_KEY=sk-...
```

## Load Balancing

### Nginx Configuration

Included in `deployment/docker-compose.yml`:

```nginx
upstream jarvis_backend {
    least_conn;  # Load balancing method
    server jarvis-app-1:8000 max_fails=3 fail_timeout=30s;
    server jarvis-app-2:8000 max_fails=3 fail_timeout=30s;
    server jarvis-app-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name jarvis.example.com;

    location / {
        proxy_pass http://jarvis_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Health check
        proxy_next_upstream error timeout http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://jarvis_backend/health;
    }
}
```

### Kubernetes Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jarvis-ingress
  namespace: jarvis
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - jarvis.example.com
    secretName: jarvis-tls
  rules:
  - host: jarvis.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: jarvis-app
            port:
              number: 80
```

## High Availability

### Database Replication

**PostgreSQL Primary-Replica**:
```yaml
# Primary (read-write)
apiVersion: v1
kind: Service
metadata:
  name: postgres-primary
spec:
  selector:
    app: postgres
    role: primary

# Replica (read-only)
apiVersion: v1
kind: Service
metadata:
  name: postgres-replica
spec:
  selector:
    app: postgres
    role: replica
```

**Connection string in app**:
```python
# Write operations
PG_HOST = "postgres-primary"

# Read operations (optional optimization)
PG_REPLICA_HOST = "postgres-replica"
```

### Redis Sentinel (High Availability)

```yaml
# Redis Sentinel for automatic failover
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-sentinel
spec:
  serviceName: redis-sentinel
  replicas: 3
  template:
    spec:
      containers:
      - name: sentinel
        image: redis:7-alpine
        command: ["redis-sentinel", "/etc/redis/sentinel.conf"]
```

### Multi-Region Deployment

```bash
# Deploy to multiple regions
regions=("us-west-2" "us-east-1" "eu-west-1")

for region in "${regions[@]}"; do
  aws eks update-kubeconfig --name jarvis-cluster-$region --region $region
  kubectl apply -f deployment/kubernetes/jarvis-deployment.yaml
done

# Global load balancer (AWS Route 53)
aws route53 create-health-check --health-check-config \
  IPAddress=<lb-ip>,Port=80,Type=HTTP,ResourcePath=/health

# GCP Global Load Balancer
gcloud compute backend-services create jarvis-backend-global \
  --protocol=HTTP \
  --health-checks=jarvis-health \
  --global
```

## Monitoring & Observability

### Prometheus Metrics

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: jarvis-metrics
  namespace: jarvis
spec:
  selector:
    matchLabels:
      app: jarvis-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboards

```bash
# Install Grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -n monitoring

# Import JARVIS dashboard
kubectl port-forward svc/grafana 3000:80 -n monitoring
# Open http://localhost:3000 and import deployment/grafana/jarvis-dashboard.json
```

### Distributed Tracing

```python
# OpenTelemetry integration (optional)
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(JaegerExporter(
        agent_host_name="jaeger-agent",
        agent_port=6831,
    ))
)
trace.set_tracer_provider(provider)
```

## Cost Optimization

### Right-Sizing

```bash
# Analyze resource usage
kubectl top pods -n jarvis --sort-by=memory
kubectl top pods -n jarvis --sort-by=cpu

# Adjust resource requests/limits based on actual usage
# Recommendation: Set requests to P50 usage, limits to P95
```

### Spot Instances (AWS)

```yaml
# Use spot instances for workers
apiVersion: v1
kind: NodePool
metadata:
  name: jarvis-workers-spot
spec:
  instanceTypes:
    - c5.xlarge
    - c5.2xlarge
  capacityType: SPOT
  taints:
    - key: workload-type
      value: batch
      effect: NoSchedule

# Tolerate spot instances
spec:
  tolerations:
  - key: workload-type
    value: batch
    effect: NoSchedule
```

### Autoscaling Based on Queue Size

```bash
# Install KEDA (Kubernetes Event-Driven Autoscaling)
kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml

# Scale workers based on Celery queue size
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaler
spec:
  scaleTargetRef:
    name: celery-worker-model
  minReplicaCount: 5
  maxReplicaCount: 50
  triggers:
  - type: redis
    metadata:
      address: redis:6379
      password: <password>
      listName: celery
      listLength: "10"
```

## Troubleshooting

### Common Issues

**Pods not starting**:
```bash
kubectl describe pod <pod-name> -n jarvis
kubectl logs <pod-name> -n jarvis --previous
```

**Database connection issues**:
```bash
# Test PostgreSQL connectivity
kubectl run -it --rm psql --image=postgres:14-alpine --restart=Never -n jarvis -- \
  psql -h postgres -U jarvis -d jarvis_kg

# Test Redis connectivity
kubectl run -it --rm redis-cli --image=redis:7-alpine --restart=Never -n jarvis -- \
  redis-cli -h redis -a <password> ping
```

**HPA not scaling**:
```bash
# Check metrics server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top pods -n jarvis

# Check HPA status
kubectl describe hpa jarvis-app-hpa -n jarvis
```

**High latency**:
```bash
# Check if pods are healthy
kubectl get pods -n jarvis -o wide

# Check resource saturation
kubectl top pods -n jarvis
kubectl top nodes

# Scale up manually if needed
kubectl scale deployment jarvis-app --replicas=10 -n jarvis
```

## Security Best Practices

1. **Never commit secrets to Git**
   ```bash
   # Use Kubernetes secrets or cloud secret managers
   # AWS Secrets Manager, Google Secret Manager, Azure Key Vault
   ```

2. **Enable network policies**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: jarvis-network-policy
   spec:
     podSelector:
       matchLabels:
         app: jarvis-app
     ingress:
     - from:
       - podSelector:
           matchLabels:
             app: nginx
     egress:
     - to:
       - podSelector:
           matchLabels:
             app: postgres
       - podSelector:
           matchLabels:
             app: redis
   ```

3. **Use private container registries**
4. **Enable pod security policies**
5. **Rotate credentials regularly**
6. **Use SSL/TLS for all connections**

## Performance Tuning

### PostgreSQL Connection Pooling

```python
# Already implemented in kg_backends.py
backend = PostgreSQLBackend(
    host="postgres",
    database="jarvis_kg",
    user="jarvis",
    password="...",
    pool_size=20,      # Adjust based on pod count
    max_overflow=40,   # Allow bursts
)
```

### Redis Pipelining

```python
# For high-throughput operations
import redis
r = redis.Redis(host='redis', password='...')
pipe = r.pipeline()
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()
```

### Celery Optimization

```python
# agent/queue_config.py
QueueConfig(
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=1000,  # Restart after 1000 tasks
    task_acks_late=True,  # Acknowledge after completion
    task_compression='gzip',  # Compress large payloads
)
```

## Next Steps

1. **Deploy to staging**: Test with `docker-compose` first
2. **Load testing**: Use `k6` or `locust` to simulate load
3. **Monitoring setup**: Configure Prometheus + Grafana
4. **Production deployment**: Deploy to Kubernetes with HPA
5. **Iterate**: Monitor metrics and adjust scaling parameters

## Support

- **Documentation**: See `POSTGRESQL_MIGRATION_GUIDE.md`, `TEMPORAL_INTEGRATION_GUIDE.md`
- **Logs**: `kubectl logs -f deployment/jarvis-app -n jarvis`
- **Metrics**: Flower UI (Celery), Temporal UI, Prometheus/Grafana
- **Issues**: Check CloudWatch Logs (AWS), Cloud Logging (GCP), Log Analytics (Azure)

---

**Summary**: JARVIS now supports production cloud deployment with:
- ✅ Docker Compose (3-5 instances)
- ✅ Kubernetes with HPA (3-50+ instances)
- ✅ Auto-scaling based on CPU/memory/custom metrics
- ✅ Load balancing with health checks
- ✅ High availability with multi-AZ deployment
- ✅ Zero-downtime rolling updates
