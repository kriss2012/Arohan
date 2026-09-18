# ISDP Platform: Deployment & Operations Manual

---

## 1. System Requirements

- **Backend Runtime**: Python 3.12+ (Python 3.14 compatible)
- **Frontend / Desktop Runtime**: Node.js 20+, Rust / Cargo 1.75+ (for Tauri desktop binaries)
- **Primary Database**: PostgreSQL 16+ with `pgvector` extension (Production)
- **Local Dev / Testing Database**: SQLite with WAL mode (Zero-dependency out-of-the-box)

---

## 2. Environment Variables Configuration (`.env.example`)

```env
# Application Core
ENVIRONMENT=development
PROJECT_NAME="Institute Student Development Platform"
API_V1_STR=/api/v1
SECRET_KEY=change-this-to-a-super-secret-hex-key-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Persistence Layer
DATABASE_URL=sqlite+aiosqlite:///./isdp_campus.db
# For PostgreSQL production:
# DATABASE_URL=postgresql+asyncpg://isdp_user:secure_password@localhost:5432/isdp_prod

# AI Layer
AI_PROVIDER=local_deterministic
# AI_PROVIDER=gemini
# AI_PROVIDER=openai
AI_MODEL=gemini-1.5-pro
AI_API_KEY=your_key_here

# Exam Mode
DESKTOP_KIOSK_ENABLED=true
MAX_INTEGRITY_TOLERANCE_COUNT=10
```

---

## 3. Running Services Locally

### Backend Server:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Web Frontend:
```powershell
cd frontend
npm run dev
```

### Native Desktop Application (Tauri):
```powershell
cd frontend
npm run tauri dev
```
