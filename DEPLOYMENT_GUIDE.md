# Deployment Guide

## Overview

This guide covers deployment of the Receipt-and-delivery system in various environments.

## Prerequisites

### Desktop Application

- Windows 10+ or Linux (Ubuntu 20.04+)
- 4GB RAM minimum
- 500MB disk space

### Web Backend

- Python 3.10+
- PostgreSQL 16+
- 2GB RAM minimum
- 1GB disk space

### Docker Deployment

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum

## Desktop Application Deployment

### Installation

1. Download `LabReceiptSystem.exe` (Windows) or `LabReceiptSystem` (Linux)
2. Run the installer
3. Follow installation wizard

### Configuration

Application creates configuration in:
- Windows: `%LOCALAPPDATA%/LabReceiptSystem/`
- Linux: `~/Documents/LabReceiptSystem/`

### First Run

1. Launch application
2. Login with default admin credentials:
   - Username: `admin`
   - Password: `admin`
3. **IMPORTANT:** Change default password immediately
4. Configure settings as needed

## Web Backend Deployment

### Local Development

```bash
# Clone repository
git clone git@github.com:samertts/Receipt-and-delivery.git
cd Receipt-and-delivery/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Environment Variables

```bash
# Required
DATABASE_URL=postgresql+psycopg://user:password@host:5432/lab_txn
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-domain.com

# Optional
LOG_LEVEL=INFO
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

#### Database Setup

```bash
# Create database
createdb -U postgres lab_txn

# Create user
createuser -U postgres lab_user
psql -U postgres -c "ALTER USER lab_user WITH PASSWORD 'your-password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE lab_txn TO lab_user;"

# Run migrations
alembic upgrade head
```

#### Running with Systemd

```ini
# /etc/systemd/system/lab-receipt.service
[Unit]
Description=Lab Receipt System API
After=network.target postgresql.service

[Service]
User=lab
Group=lab
WorkingDirectory=/opt/Receipt-and-delivery/backend
Environment=PATH=/opt/Receipt-and-delivery/backend/.venv/bin
ExecStart=/opt/Receipt-and-delivery/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable lab-receipt
sudo systemctl start lab-receipt
```

## Docker Deployment

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Create environment file
cp .env.example .env
# Edit .env with production settings

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| db | 5432 | PostgreSQL database |
| backend | 8000 | FastAPI backend |
| frontend | 80 | Vue.js frontend (nginx) |

## Frontend Deployment

### Development

```bash
cd frontend
npm install
npm run dev  # Runs on port 5173
```

### Production Build

```bash
cd frontend
npm install
npm run build  # Creates dist/ directory
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /opt/Receipt-and-delivery/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## SSL/TLS Configuration

### Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check readiness
curl http://localhost:8000/api/health/ready

# Check dependencies
curl http://localhost:8000/api/health/dependencies
```

### Log Monitoring

```bash
# Docker logs
docker-compose logs -f backend

# Systemd logs
journalctl -u lab-receipt -f
```

## Backup Strategy

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U lab_user lab_txn > /backups/lab_txn_$DATE.sql
```

### Automated Backup

```bash
# Add to crontab
0 2 * * * /opt/scripts/backup_lab.sh
```

## Scaling

### Horizontal Scaling

1. Deploy multiple backend instances
2. Use load balancer (nginx, HAProxy)
3. Shared PostgreSQL database
4. Redis for session/cache sharing

### Vertical Scaling

1. Increase PostgreSQL resources
2. Increase backend server resources
3. Optimize connection pooling

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Database connection failed | Check PostgreSQL is running, verify credentials |
| Port already in use | Change port in configuration |
| Permission denied | Check file permissions, run as correct user |
| Out of memory | Increase server resources |
| Slow queries | Check database indexes, optimize queries |

### Log Analysis

```bash
# Search for errors
grep -i error /var/log/lab-receipt/*.log

# Search for slow queries
grep -i "slow" /var/log/lab-receipt/*.log
```

## Rollback Procedure

### Database Rollback

1. Stop application
2. Restore database from backup
3. Run migrations if needed
4. Start application

### Application Rollback

1. Stop application
2. Deploy previous version
3. Start application
4. Verify functionality

## Security Checklist

- [ ] Change default admin password
- [ ] Configure strong SECRET_KEY
- [ ] Enable SSL/TLS
- [ ] Restrict database access
- [ ] Configure firewall
- [ ] Enable audit logging
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test recovery procedures
