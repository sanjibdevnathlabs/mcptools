# Production Deployment Guide

This guide covers deploying the Database MCP Server in production environments with proper security, monitoring, and operational practices.

## Quick Start Deployment

### Minimal Production Setup

**Step 1: Create minimal configuration**
```bash
# /opt/database-mcp/.env
DATABASE_USER=prod_user
DATABASE_PASSWORD=secure_password
DATABASE_HOST=prod-mysql.company.com
DATABASE_USE_SSL=true
```

**Step 2: Start the server**
```bash
python -m database --transport streamable-http --port 8080
```

**That's it!** You now have a production-ready MCP server with:
- ✅ SSL/TLS database connections
- ✅ HTTP transport for web applications
- ✅ 8 core tools (optimal for most use cases)
- ✅ All security features enabled by default

## Transport Mode Selection

Choose the right transport mode for your deployment:

| Transport Mode | Use Case | Port Required | Best For |
|----------------|----------|---------------|----------|
| `stdio` | CLI integration | No | Cursor/Copilot, uvx clients |
| `streamable-http` | HTTP APIs | Yes | Web apps, MCP Inspector |
| `sse` | Real-time streaming | Yes | Event-driven applications |
| `auto` | Automatic detection | Maybe | Mixed environments |

### Transport Configuration Examples

**Stdio (Default):**
```bash
# .env
DATABASE_USER=api_user
DATABASE_PASSWORD=api_password
# SERVER_TRANSPORT_MODE=stdio (default)

# Start server
python -m database
```

**Streamable HTTP:**
```bash
# .env
DATABASE_USER=api_user
DATABASE_PASSWORD=api_password
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# Start server
python -m database --transport streamable-http
```

**SSE:**
```bash
# .env
DATABASE_USER=api_user
DATABASE_PASSWORD=api_password
SERVER_TRANSPORT_MODE=sse
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# Start server
python -m database --transport sse
```

## Deployment Architectures

### 1. Standalone Deployment

**Simple single-server deployment for small to medium applications:**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Database MCP    │───▶│   MySQL/MariaDB │
│                 │    │     Server       │    │    Database     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Configuration:**
```bash
# .env
DATABASE_USER=app_user
DATABASE_PASSWORD=app_password
DATABASE_HOST=localhost
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
MCP_TOOL_MODE=lite
```

**Installation:**
```bash
# Create application directory
sudo mkdir -p /opt/database-mcp
cd /opt/database-mcp

# Install application
pip install database-mcp
# or clone from repository

# Create configuration
cp docs/env.example .env
# Edit .env with your settings

# Create systemd service
sudo tee /etc/systemd/system/database-mcp.service > /dev/null <<EOF
[Unit]
Description=Database MCP Server
After=network.target mysql.service

[Service]
Type=simple
User=mcp
Group=mcp
WorkingDirectory=/opt/database-mcp
ExecStart=/opt/database-mcp/venv/bin/python -m database --transport streamable-http
Restart=always
RestartSec=10
Environment=PATH=/opt/database-mcp/venv/bin

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl enable database-mcp
sudo systemctl start database-mcp
```

### 2. Load-Balanced Deployment

**High-availability deployment with multiple MCP server instances:**

```
                    ┌──────────────────┐
                    │   Load Balancer  │
                    │   (nginx/HAProxy)│
                    └─────────┬────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   MCP Server    │   │   MCP Server    │   │   MCP Server    │
│   Instance 1    │   │   Instance 2    │   │   Instance 3    │
└─────────┬───────┘   └─────────┬───────┘   └─────────┬───────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                        ┌───────▼────────┐
                        │  MySQL Cluster │
                        │   (Primary/     │
                        │   Replicas)     │
                        └────────────────┘
```

**Nginx Load Balancer Configuration:**
```nginx
# /etc/nginx/sites-available/database-mcp
upstream database_mcp {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
    server 10.0.1.12:8080;
}

server {
    listen 80;
    server_name api.company.com;

    location / {
        proxy_pass http://database_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**MCP Server Configuration (each instance):**
```bash
# .env (per instance)
DATABASE_USER=app_user
DATABASE_PASSWORD=app_password
DATABASE_HOST=mysql-cluster.internal
DATABASE_USE_SSL=true
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
MCP_TOOL_MODE=full

# Performance tuning
DATABASE_POOL_MAXSIZE=25
MCP_MAX_QUERIES_PER_MINUTE=500

# Monitoring
MONITORING_ENABLE_METRICS=true
LOG_ENABLE_FILE_LOGGING=true
```

### 3. Containerized Deployment (Docker)

**Docker-based deployment for scalability and orchestration:**

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash mcp

# Set working directory
WORKDIR /app

# Copy application
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to application user
USER mcp

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -m database --test-query "SELECT 1" || exit 1

# Start application
CMD ["python", "-m", "database", "--transport", "streamable-http"]
```

**Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  database-mcp:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_USER=app_user
      - DATABASE_PASSWORD=app_password
      - DATABASE_HOST=mysql
      - SERVER_TRANSPORT_MODE=streamable-http
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8080
      - MCP_TOOL_MODE=lite
    depends_on:
      mysql:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=app_db
      - MYSQL_USER=app_user
      - MYSQL_PASSWORD=app_password
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10
    restart: unless-stopped

volumes:
  mysql_data:
```

**Start deployment:**
```bash
# Start services
docker-compose up -d

# Check health
docker-compose ps
docker-compose logs database-mcp

# Scale MCP servers
docker-compose up -d --scale database-mcp=3
```

### 4. Kubernetes Deployment

**Cloud-native deployment with Kubernetes:**

**ConfigMap:**
```yaml
# database-mcp-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-mcp-config
data:
  DATABASE_HOST: "mysql-service"
  SERVER_TRANSPORT_MODE: "streamable-http"
  SERVER_HOST: "0.0.0.0" 
  SERVER_PORT: "8080"
  MCP_TOOL_MODE: "lite"
  MONITORING_ENABLE_METRICS: "true"
  LOG_ENABLE_FILE_LOGGING: "true"
```

**Secret:**
```yaml
# database-mcp-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-mcp-secret
type: Opaque
stringData:
  DATABASE_USER: "app_user"
  DATABASE_PASSWORD: "secure_password"
```

**Deployment:**
```yaml
# database-mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-mcp
  labels:
    app: database-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: database-mcp
  template:
    metadata:
      labels:
        app: database-mcp
    spec:
      containers:
      - name: database-mcp
        image: database-mcp:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: database-mcp-config
        - secretRef:
            name: database-mcp-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Service:**
```yaml
# database-mcp-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: database-mcp-service
spec:
  selector:
    app: database-mcp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
```

**Deploy to Kubernetes:**
```bash
# Apply configurations
kubectl apply -f database-mcp-config.yaml
kubectl apply -f database-mcp-secret.yaml
kubectl apply -f database-mcp-deployment.yaml
kubectl apply -f database-mcp-service.yaml

# Check deployment
kubectl get pods -l app=database-mcp
kubectl get svc database-mcp-service
```

## Security Configuration

### 1. Database Security

**SSL/TLS Configuration:**
```bash
# .env
DATABASE_USE_SSL=true
DATABASE_SSL_CA=/etc/ssl/mysql-ca.pem
DATABASE_SSL_CERT=/etc/ssl/mysql-client-cert.pem
DATABASE_SSL_KEY=/etc/ssl/mysql-client-key.pem
DATABASE_VERIFY_SSL=true
```

**User Permissions:**
```sql
-- Create dedicated database user
CREATE USER 'mcp_user'@'%' IDENTIFIED BY 'secure_password';

-- Grant minimal required permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'mcp_user'@'%';
GRANT SHOW DATABASES ON *.* TO 'mcp_user'@'%';

-- For read-only deployments
GRANT SELECT, SHOW DATABASES ON *.* TO 'mcp_readonly'@'%';

FLUSH PRIVILEGES;
```

### 2. Application Security

**Enhanced Security Configuration:**
```bash
# .env
# SQL injection protection
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true
SECURITY_AUDIT_LOGGING=true

# Read-only mode for sensitive environments
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]

# Rate limiting
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=100

# HTTP authentication (for HTTP transports)
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=api_client
SECURITY_PASSWORD=secure_api_token

# IP restrictions
SECURITY_ENABLE_IP_WHITELIST=true
SECURITY_ALLOWED_IPS=10.0.0.0/8,192.168.1.0/24
```

### 3. Network Security

**Firewall Configuration:**
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 8080/tcp      # MCP Server
sudo ufw allow from 10.0.0.0/8 to any port 3306  # MySQL (internal only)
sudo ufw enable

# iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP
```

**Reverse Proxy with SSL:**
```nginx
# /etc/nginx/sites-available/database-mcp-ssl
server {
    listen 443 ssl http2;
    server_name api.company.com;

    ssl_certificate /etc/ssl/certs/api.company.com.crt;
    ssl_certificate_key /etc/ssl/private/api.company.com.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.company.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring and Observability

### 1. Application Monitoring

**Health Check Endpoint:**
```bash
# Check server health
curl http://localhost:8080/health

# Response format:
{
  "status": "healthy",
  "database_connection": "ok",
  "response_time_ms": 45,
  "timestamp": "2024-08-16T20:30:00Z",
  "details": {
    "pool_active": 2,
    "pool_size": 10,
    "uptime_seconds": 3600
  }
}
```

**Metrics Collection:**
```bash
# .env
MONITORING_ENABLE_METRICS=true
MONITORING_METRICS_INTERVAL=60
MONITORING_TRACK_MEMORY_USAGE=true
MONITORING_TRACK_CPU_USAGE=true
MONITORING_TRACK_CONNECTION_POOL=true
```

### 2. Logging Configuration

**Production Logging:**
```bash
# .env
LOG_ENABLE_FILE_LOGGING=true
LOG_DIRECTORY=/var/log/database-mcp
LOG_MAX_FILE_SIZE=100MB
LOG_BACKUP_COUNT=10

# Component log levels
LOG_LEVEL_DATABASE=INFO
LOG_LEVEL_SECURITY=WARNING
LOG_LEVEL_MONITORING=INFO
SERVER_LOG_LEVEL=INFO
```

**Log Rotation with logrotate:**
```bash
# /etc/logrotate.d/database-mcp
/var/log/database-mcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    postrotate
        systemctl reload database-mcp
    endscript
}
```

### 3. Prometheus Integration

**Metrics Endpoint:**
```bash
# Enable Prometheus metrics
MONITORING_ENABLE_METRICS=true

# Scrape endpoint
curl http://localhost:8080/metrics
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'database-mcp'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Grafana Dashboard:**
- Connection pool utilization
- Query response times
- Error rates
- System resource usage
- Security events

## Performance Optimization

### 1. Connection Pool Tuning

**High-Traffic Configuration:**
```bash
# .env
DATABASE_POOL_MINSIZE=10
DATABASE_POOL_MAXSIZE=50
DATABASE_POOL_RECYCLE=1800

# Timeout optimization
DATABASE_CONNECT_TIMEOUT=15.0
DATABASE_READ_TIMEOUT=60.0
DATABASE_WRITE_TIMEOUT=60.0
DATABASE_QUERY_TIMEOUT=120.0
```

**Connection Pool Monitoring:**
```sql
-- Monitor MySQL connections
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';
SHOW VARIABLES LIKE 'max_connections';

-- Check for connection leaks
SHOW PROCESSLIST;
```

### 2. Query Performance

**Query Optimization Settings:**
```bash
# .env
# Enable query caching
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Query limits
DATABASE_MAX_ROWS_LIMIT=10000
DATABASE_QUERY_TIMEOUT=60.0

# Development tools
DEV_ENABLE_QUERY_EXPLAIN=true
```

### 3. Resource Optimization

**System Resource Monitoring:**
```bash
# .env
MONITORING_TRACK_MEMORY_USAGE=true
MONITORING_TRACK_CPU_USAGE=true

# Circuit breaker for protection
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

## Backup and Recovery

### 1. Configuration Backup

**Backup Script:**
```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/backup/database-mcp/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp /opt/database-mcp/.env "$BACKUP_DIR/"
cp -r /opt/database-mcp/logs "$BACKUP_DIR/" 2>/dev/null || true

# Backup application code
tar -czf "$BACKUP_DIR/application.tar.gz" /opt/database-mcp --exclude=logs --exclude=venv

echo "Backup completed: $BACKUP_DIR"
```

### 2. Disaster Recovery

**Recovery Procedures:**

1. **Service Recovery:**
```bash
# Stop service
sudo systemctl stop database-mcp

# Restore configuration
cp /backup/database-mcp/latest/.env /opt/database-mcp/

# Restart service
sudo systemctl start database-mcp
```

2. **Database Recovery:**
```bash
# Test database connectivity
python -m database --test-query "SELECT 1"

# Verify schema access
python -m database --test-query "SHOW DATABASES"
```

## Maintenance Procedures

### 1. Updates and Upgrades

**Update Process:**
```bash
# 1. Backup current installation
./backup-config.sh

# 2. Stop service
sudo systemctl stop database-mcp

# 3. Update application
cd /opt/database-mcp
git pull origin main
pip install -r requirements.txt

# 4. Update configuration if needed
# Check for new environment variables in docs/env.example

# 5. Test configuration
python -m database --test-tools

# 6. Start service
sudo systemctl start database-mcp

# 7. Verify operation
curl http://localhost:8080/health
```

### 2. Log Management

**Log Cleanup:**
```bash
#!/bin/bash
# cleanup-logs.sh

LOG_DIR="/var/log/database-mcp"
RETENTION_DAYS=30

# Remove old log files
find "$LOG_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete
find "$LOG_DIR" -name "*.log.gz" -mtime +$RETENTION_DAYS -delete

echo "Log cleanup completed"
```

### 3. Security Audits

**Regular Security Checks:**
```bash
# Check for security updates
sudo apt update && sudo apt list --upgradable

# Review security logs
grep -i "security\|blocked\|denied" /var/log/database-mcp/*.log

# Test security configuration
python -c "
import requests
# Test rate limiting, authentication, etc.
"

# Review database permissions
mysql -e "SELECT user, host FROM mysql.user WHERE user = 'mcp_user';"
```

## Troubleshooting

### Common Issues

1. **Connection Refused:**
```bash
# Check if service is running
sudo systemctl status database-mcp

# Check port binding
netstat -tlpn | grep 8080

# Check firewall
sudo ufw status
```

2. **Database Connection Issues:**
```bash
# Test direct database connection
mysql -h $DATABASE_HOST -u $DATABASE_USER -p

# Check SSL configuration
openssl s_client -connect $DATABASE_HOST:3306 -starttls mysql
```

3. **Performance Issues:**
```bash
# Check resource usage
top -p $(pgrep -f "python -m database")

# Monitor connection pool
curl http://localhost:8080/tools/call -d '{"name": "connection_stats"}'
```

### Debug Mode

**Enable Debug Logging:**
```bash
# Temporary debug mode
SERVER_DEBUG=true SERVER_LOG_LEVEL=DEBUG python -m database

# Production debug (restart required)
echo "SERVER_DEBUG=true" >> .env
echo "SERVER_LOG_LEVEL=DEBUG" >> .env
sudo systemctl restart database-mcp
```

This deployment guide provides comprehensive coverage for deploying the Database MCP Server in various production environments. For additional help, see the [Configuration Guide](CONFIGURATION.md) and [Environment Variables Reference](ENVIRONMENT.md).
