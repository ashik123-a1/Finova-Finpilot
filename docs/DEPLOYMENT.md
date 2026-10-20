# FinTechathon 2026: SME Finance Copilot — Local & Production Deployment Guide

**Document Version:** 1.0.0 (Master Release)  
**Primary Topology:** Local-First High-Performance ASGI Application  
**Port:** `8050` (Configurable via `PORT` environment variable)

---

## 1. Local-First Evaluation Deployment

The primary evaluation topology for FinTechathon 2026 is a local bare-metal or virtualized environment.

### 1-Click Launch (Windows)
Double-click `start.bat` in the root directory or execute in PowerShell:
```powershell
cd "F:\china project"
.\start.bat
```
*Applies database migrations, performs integrity checks, and starts Uvicorn on `http://127.0.0.1:8050`.*

### Manual Startup (Cross-Platform)
```bash
# Windows
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8050

# Linux / macOS
uvicorn src.api.app:app --host 0.0.0.0 --port 8050 --workers 4
```

---

## 2. Production ASGI Flags & Performance Configuration

When deploying in production server environments (e.g. Linux VPS or Docker container):

```bash
uvicorn src.api.app:app \
  --host 0.0.0.0 \
  --port 8050 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --proxy-headers \
  --forwarded-allow-ips "*" \
  --timeout-keep-alive 65 \
  --access-log
```

---

## 3. Containerization Readiness (Dockerfile Reference)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure storage directories exist
RUN mkdir -p var/backups var/exports storage/uploads

EXPOSE 8050

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8050"]
```

---

## 4. Live Cloudflare Tunnel Deployment (Optional Remote Evaluation)

For remote judges or mobile evaluation without public port forwarding:
```powershell
cd "F:\china project"
.\share_online.bat
```
*Spins up an encrypted Cloudflare tunnel forwarding traffic directly to `http://127.0.0.1:8050` with an HTTPS URL recorded in `LIVE_ONLINE_LINK.txt`.*
