# Local Database Architecture & Offline LAN Topology

**System**: Institute Student Development Platform (ISDP)  
**Deployment Mode**: Offline Local Institutional LAN (Zero Internet/Cloud Dependency)  
**Database Engines**: Local PostgreSQL 16+ / Local High-Concurrency SQLite 3.50+ with WAL mode  

---

## 1. Network Topology (Institute Controlled)

```mermaid
graph TD
    subgraph Campus LAN Environment
        AdminClient["Institutional Admin Console (Tauri Desktop / Web)"]
        FacultyClient["Faculty Workstations (Tauri Desktop / Web)"]
        StudentClient["Student Laboratory PCs (ISDP Desktop Kiosk)"]
    end

    subgraph Institute Dedicated Local Server
        LocalAPI["Local FastAPI Server (Port 8000)"]
        LocalDB[("Local PostgreSQL / SQLite DB (Port 5432)")]
        LocalStorage["Local Filesystem Storage (C:\\InstituteLMS\\storage)"]
        LocalBackup["Local Backup Vault (C:\\InstituteLMS\\backups)"]
        LocalAI["Local AROHAN Diagnostics Engine"]
    end

    AdminClient -->|Local LAN HTTP/WS| LocalAPI
    FacultyClient -->|Local LAN HTTP/WS| LocalAPI
    StudentClient -->|Local LAN HTTP/WS| LocalAPI

    LocalAPI --> LocalDB
    LocalAPI --> LocalStorage
    LocalAPI --> LocalAI
    LocalAPI --> LocalBackup
```

---

## 2. Core Architectural Tenets

1. **No External SaaS / Cloud Database**: Strictly prohibits Supabase, Firebase, AWS RDS, Neon, or PlanetScale. All student and institutional data resides exclusively on institute premises.
2. **Zero Internet Requirement**: Authentication, exam conduct, assignments, file uploads, progress calculation, and backups function 100% offline.
3. **Authorized Email Allowlist**: Only pre-authorized email addresses placed in `authorized_users` by an administrator can register or activate accounts via local activation codes.
4. **Relational Integrity**: Enforces strict foreign keys, unique email/roll/employee constraints, check constraints, composite indexes, and immutable audit streams.
