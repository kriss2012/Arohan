# Offline Campus Deployment Guide

## 1. Network Topology
```
                     INSTITUTIONAL CAMPUS LAN (NO INTERNET REQUIRED)
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
            Admin Terminal          Faculty Workstation       Student Lab PC
           (Desktop App/Web)        (Desktop App/Web)       (Desktop Kiosk Mode)
                  │                       │                       │
                  └───────────────────────┼───────────────────────┘
                                          │
                                          ▼
                               Local Campus Server
                             (Host: 192.168.1.100)
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                               ▼
                   FastAPI Backend               Local PostgreSQL 16
                   (Port 8000)                   (Port 5432)
                          │                               │
                          ▼                               ▼
                 Local File Storage               Local Backup Vault
                 (C:\InstituteLMS\storage)        (C:\InstituteLMS\backups)
```

## 2. Docker Compose Deployment
To launch the stack on an institutional local server:
```bash
docker compose up -d
```
Services included:
- `isdp-db`: Local PostgreSQL 16 container with persistent volumes.
- `isdp-redis`: Local in-memory caching and session store.
- `isdp-backend`: FastAPI application container.

## 3. Windows PowerShell Operations Scripts
Under `scripts/`:
- `scripts/install.ps1`: Creates directories and dependencies.
- `scripts/setup.ps1`: Initializes database and seeds default admin persona.
- `scripts/start.ps1`: Starts local services without internet.
- `scripts/stop.ps1`: Cleanly halts processes.
- `scripts/backup.ps1`: Executes full offline backup.
- `scripts/restore.ps1`: Safe restore from local backup zip.
- `scripts/health-check.ps1`: Pings `/health` and monitors storage.
