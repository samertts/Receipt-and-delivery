# Deployment Guide — Ubuntu 22.04 LTS (Production)

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start (Docker Compose)](#2-quick-start-docker-compose)
3. [Manual Bare-Metal Deployment](#3-manual-bare-metal-deployment)
4. [Nginx Reverse Proxy with SSL](#4-nginx-reverse-proxy-with-ssl)
5. [Environment Configuration](#5-environment-configuration)
6. [Database Setup & Migrations](#6-database-setup--migrations)
7. [Systemd Services](#7-systemd-services)
8. [Firewall & Security Hardening](#8-firewall--security-hardening)
9. [Backup & Restore](#9-backup--restore)
10. [Logging & Monitoring](#10-logging--monitoring)
11. [Updating](#11-updating)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### System Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    curl wget git \
    python3 python3-pip python3-venv \
    postgresql postgresql-client \
    nginx \
    certbot python3-certbot-nginx \
    ufw \
    redis-server \
    libpq-dev
```

### Node.js 20 LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

### Python Virtual Environment (if not using Docker)

```bash
sudo apt install -y python3.12 python3.12-venv  # or use system Python 3.10
```

---

## 2. Quick Start (Docker Compose — Production)

The production stack uses `docker-compose.prod.yml` with:

| Service | Image | Role |
|---|---|---|
| `db` | `postgres:16-alpine` | PostgreSQL with tuned config |
| `backend` | Custom `backend/Dockerfile` | FastAPI via uvicorn workers, auto‑runs `init_db()` on start |
| `frontend` | Custom `frontend/Dockerfile` | Multi‑stage build: Vite produces static files → nginx:alpine serves them + proxies `/api/` to backend |

No separate nginx reverse proxy is needed — the frontend container includes it. API calls from the SPA go to `/api/*` (same origin), and nginx forwards them to the backend. CORS is not needed in production since there's no cross-origin traffic.

### 2.1 Install Docker

```bash
# Docker Engine
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose plugin
sudo apt install -y docker-compose-plugin
```

### 2.2 Clone & Prepare

```bash
cd /opt
sudo git clone <your-repo-url> lab-receipt-system
sudo chown -R $USER:$USER lab-receipt-system
cd lab-receipt-system
cp deploy/.env.prod.example .env
chmod 600 .env
```

### 2.3 Configure `.env`

Edit `.env` and fill in the required values:

```ini
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
POSTGRES_PASSWORD=<generate a strong random password>
```

All other variables have sensible defaults. See `deploy/.env.prod.example` for the full list.

### 2.4 Build and Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

### 2.5 Create Initial Admin User

```bash
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.services.user import create_user
db = SessionLocal()
create_user(db, email='admin@example.com', password='<strong-password>', is_superuser=True)
db.close()
"
```

### 2.6 Verify

```bash
curl http://localhost/api/health
```

The frontend is available at `http://<server-ip>` (port 80).

### 2.7 Production Architecture

```
                         Internet
                            |
                         [UFW: 80, 443]
                            |
                    [frontend:80 (nginx)]
                      /              \
            serves /                  proxies /api/
        /usr/share/nginx/html      → http://backend:8000
          (Vue SPA, static)              |
                                     [FastAPI]
                                         |
                                     [PostgreSQL]
```

---

## 3. Manual Bare-Metal Deployment

For greater control or when Docker is not an option.

### 3.1 PostgreSQL Setup

```bash
sudo -u postgres psql
```

```sql
CREATE USER lab_user WITH PASSWORD '<strong-password>';
CREATE DATABASE lab_txn OWNER lab_user;
\c lab_txn
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### 3.2 Frontend Build

```bash
cd /opt/lab-receipt-system/frontend
npm ci
npm run build
```

The output is in `frontend/dist/`. This will be served by Nginx.

### 3.3 Backend Setup

```bash
cd /opt/lab-receipt-system/backend
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# Create a production .env
cp ../.env.example .env
# Edit .env with production values
```

Ensure `DATABASE_URL` in `.env` points to the local PostgreSQL:

```ini
DATABASE_URL=postgresql+psycopg://lab_user:<strong-password>@localhost:5432/lab_txn
```

### 3.4 Run Migrations

```bash
cd /opt/lab-receipt-system/backend
source venv/bin/activate
alembic upgrade head
```

### 3.5 Create Storage Directory

```bash
mkdir -p /opt/lab-receipt-system/backend/storage
sudo chown -R $USER:$USER /opt/lab-receipt-system/backend/storage
```

---

## 4. Nginx Reverse Proxy with SSL

This section applies to both Docker and bare-metal deployments. The proxy sits in front of the FastAPI backend (port 8000) and serves the built frontend static files.

### 4.1 Nginx Configuration

Create `/etc/nginx/sites-available/lab`:

```nginx
server {
    listen 80;
    server_name lab.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lab.yourdomain.com;

    # SSL — replace with your cert paths or use certbot (Section 4.2)
    ssl_certificate     /etc/letsencrypt/live/lab.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lab.yourdomain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend static files
    root /opt/lab-receipt-system/frontend/dist;
    index index.html;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml image/svg+xml;
    gzip_min_length 256;

    # PWA service worker — never cache
    location ~* (service-worker\.js)$ {
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }

    # Static assets with long cache
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # PWA icons
    location /icons/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback — all non-file routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;

        # Increase body size for file uploads
        client_max_body_size 50M;
    }

    # API docs (optional — restrict in production)
    location /api/docs {
        proxy_pass http://127.0.0.1:8000/api/docs;
        proxy_set_header Host $host;
        # Uncomment to restrict docs access by IP
        # allow 10.0.0.0/8;
        # allow 192.168.0.0/16;
        # deny all;
    }

    location /api/redoc {
        proxy_pass http://127.0.0.1:8000/api/redoc;
        proxy_set_header Host $host;
    }

    # Health check (internal)
    location /api/health {
        proxy_pass http://127.0.0.1:8000/api/health;
        proxy_set_header Host $host;
        access_log off;
    }

    # Storage files served by backend (do not serve directly from disk)
    location /storage/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/lab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.2 SSL with Let's Encrypt

```bash
sudo certbot --nginx -d lab.yourdomain.com --non-interactive --agree-tos -m admin@yourdomain.com
```

Auto-renewal is enabled by default. Test it:

```bash
sudo certbot renew --dry-run
```

---

## 5. Environment Configuration

Create an environment file that will be used by the systemd services (see Section 7).

```bash
sudo mkdir -p /etc/lab-system
sudo cp /opt/lab-receipt-system/backend/.env /etc/lab-system/env
sudo chmod 600 /etc/lab-system/env
```

The `.env` file **must** include:

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | JWT signing key (generate with `secrets.token_hex(32)`) | `a1b2c3...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user:pass@localhost:5432/lab_txn` |
| `ALLOWED_ORIGINS` | Comma-separated allowed CORS origins | `https://lab.yourdomain.com` |
| `DEBUG` | Must be `false` in production | `false` |
| `LOG_LEVEL` | `INFO` or `WARNING` | `INFO` |
| `STORAGE_ROOT` | Path to uploaded files directory | `storage` |

---

## 6. Database Setup & Migrations

### 6.1 PostgreSQL Tuning (Production)

Edit `/etc/postgresql/14/main/postgresql.conf`:

```ini
listen_addresses = 'localhost'
max_connections = 100
shared_buffers = 256MB          # ~25% of RAM
effective_cache_size = 768MB    # ~50% of RAM
work_mem = 8MB
maintenance_work_mem = 64MB
wal_level = replica
max_wal_size = 1GB
min_wal_size = 256MB
random_page_cost = 1.1          # SSD optimization
```

Restart:

```bash
sudo systemctl restart postgresql
```

### 6.2 Initialize Database Schema

The backend automatically runs `Base.metadata.create_all()` on startup via `start.sh`. No manual migration step is needed for the initial deployment.

To initialize manually (e.g. before starting the service):

```bash
cd /opt/lab-receipt-system/backend
source venv/bin/activate
python -c "from app.db.session import init_db; init_db()"
```

### 6.3 Seed Initial Data

```bash
cd /opt/lab-receipt-system/backend
source venv/bin/activate
python -c "
from app.db.session import SessionLocal
from app.services.user import create_user
db = SessionLocal()
create_user(db, email='admin@example.com', password='<strong-password>', is_superuser=True)
db.close()
"
```

---

## 7. Systemd Services

### 7.1 Backend Service

Create `/etc/systemd/system/lab-backend.service`:

```ini
[Unit]
Description=Lab Receipt System — FastAPI Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/lab-receipt-system/backend
EnvironmentFile=/etc/lab-system/env
ExecStart=/opt/lab-receipt-system/backend/venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-level info
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=process
Restart=always
RestartSec=10

# Security hardening
ProtectHome=true
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true
ReadWritePaths=/opt/lab-receipt-system/backend/storage

[Install]
WantedBy=multi-user.target
```

### 7.2 Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable lab-backend
sudo systemctl start lab-backend
sudo systemctl status lab-backend
```

### 7.3 Useful Service Commands

```bash
sudo journalctl -u lab-backend -f          # tail logs
sudo systemctl restart lab-backend         # restart
sudo systemctl reload lab-backend          # graceful reload
```

---

## 8. Firewall & Security Hardening

### 8.1 UFW (Uncomplicated Firewall)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh                 # port 22
sudo ufw allow http                # port 80
sudo ufw allow https               # port 443
sudo ufw --force enable
sudo ufw status verbose
```

### 8.2 Fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
```

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[lab-backend]
enabled = true
port = http,https
filter = lab-backend
logpath = /var/log/syslog
maxretry = 10
```

### 8.3 Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### 8.4 Disable Root Login & Password Auth (SSH)

Edit `/etc/ssh/sshd_config`:

```ini
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:

```bash
sudo systemctl restart sshd
```

---

## 9. Backup & Restore

### 9.1 Database Backup Script

Create `/usr/local/bin/backup-lab.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/lab-system"
DB_NAME="lab_txn"
DB_USER="lab_user"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Dump database
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

# Backup uploaded files
tar czf "$BACKUP_DIR/storage_${TIMESTAMP}.tar.gz" -C /opt/lab-receipt-system/backend storage

# Remove backups older than retention period
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "storage_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: ${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
```

Make it executable and add a cron job:

```bash
sudo chmod +x /usr/local/bin/backup-lab.sh
sudo crontab -e
```

Add:

```cron
0 3 * * * /usr/local/bin/backup-lab.sh
```

### 9.2 Restore

```bash
# Database
gunzip -c /var/backups/lab-system/db_20250101_030000.sql.gz | psql -U lab_user -d lab_txn

# Files
sudo tar xzf /var/backups/lab-system/storage_20250101_030000.tar.gz -C /opt/lab-receipt-system/backend
```

### 9.3 Offsite Backup (Optional)

Install `rclone` and copy backups to S3 or another provider:

```bash
sudo apt install -y rclone
rclone config  # interactive setup
```

Add to crontab:

```cron
30 3 * * * rclone copy /var/backups/lab-system remote:lab-backups/
```

---

## 10. Logging & Monitoring

### 10.1 Log Rotation

Create `/etc/logrotate.d/lab-system`:

```
/var/log/lab-system/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 10.2 Prometheus Node Exporter (Optional)

```bash
sudo apt install -y prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
```

### 10.3 Application Health Check

The backend exposes `GET /api/health`. Monitor with any external uptime service.

---

## 11. Updating

### 11.1 Bare-Metal Update

```bash
cd /opt/lab-receipt-system
sudo -u www-data git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
alembic upgrade head
sudo systemctl restart lab-backend

# Frontend
cd ../frontend
npm ci
npm run build
sudo systemctl reload nginx
```

### 11.2 Docker Update

```bash
cd /opt/lab-receipt-system
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d --force-recreate
docker image prune -f
```

---

## 12. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `502 Bad Gateway` | Backend not running | `sudo systemctl status lab-backend` or `docker compose -f docker-compose.prod.yml ps` |
| `Connection refused` (DB) | PostgreSQL not started or wrong credentials | Check `DATABASE_URL` and `sudo systemctl status postgresql` |
| CORS errors in browser | `ALLOWED_ORIGINS` missing the domain | Update `.env` and restart backend |
| `413 Request Entity Too Large` | Nginx `client_max_body_size` too small | Increase in nginx config |
| Frontend shows blank page | Build output mismatch or SPA fallback missing | Verify `try_files $uri $uri/ /index.html;` in nginx |
| PWA not installing | Missing service worker or HTTPS required | Ensure HTTPS and check `manifest.json` is served |
| Slow queries | Missing DB indexes | Run `ANALYZE;` in PostgreSQL and check slow query log |
| `permission denied` on storage | Wrong owner on storage directory | `sudo chown -R www-data:www-data storage/` |

---

## Architecture Overview

### Docker Production

```
                         Internet
                            |
                         [UFW: 80, 443]
                            |
                    [frontend:80 (nginx)]
                      /              \
            serves static files    proxies /api/
          (Vue SPA from build)   → http://backend:8000
                                       |
                                   [FastAPI]
                                  (uvicorn x4)
                                       |
                                   [PostgreSQL]
                                 (port 5432)
```

### Bare-Metal Production

```
                         Internet
                            |
                         [UFW: 80, 443]
                            |
                       [Nginx (SSL termination)]
                         /        \
                        /          \
            /opt/lab-receipt/    127.0.0.1:8000
            frontend/dist/     [uvicorn x 4 workers]
           (static files)           |
                                [PostgreSQL]
                              (localhost:5432)
```

---

## Port Reference

| Port | Service | Bound To | Purpose |
|---|---|---|---|
| 22 | SSH | 0.0.0.0 | Secure shell access |
| 80 | Nginx (frontend container) | 0.0.0.0 | HTTP frontend + API proxy |
| 443 | Nginx (host, bare-metal) | 0.0.0.0 | HTTPS (production traffic) |
| 5432 | PostgreSQL | 127.0.0.1 (container) | Database (not exposed) |
| 8000 | uvicorn | container internal | FastAPI backend (not exposed) |
| 9100 | node_exporter | 127.0.0.1 | Metrics (optional) |
