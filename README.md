# AROHAN ISDP — Institutional Campus LMS Platform
### RC Patel Educational Trust's Institute of Management Research and Development (IMRD), Shirpur

**AROHAN ISDP** (Institute Student Development Platform) is a unified academic learning management system, MCAT proctored aptitude engine, and Bayesian Knowledge Tracing (BKT) skill diagnostic platform engineered for local institutional autonomy and high-availability campus operations.

---

## 🚀 Quick Start — One-Click Launch on Any Device & OS

### 🪟 Windows (Any PC / Laptop)
Simply **double-click** either of the launcher scripts in the project folder:
- **`Launch-Arohan.bat`** (or **`run.bat`**)

> **What happens automatically:**
> 1. Detects Python 3 (3.10+). If Python is missing, offers a direct link to download it.
> 2. Automatically sets up an isolated virtual environment (`.venv`).
> 3. Automatically checks and downloads all required packages (`fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`, `pydantic`, etc.) from `requirements.txt`.
> 4. Verifies storage directories and pre-built frontend distribution.
> 5. Initializes database tables and automatically seeds institutional data.
> 6. Starts the server on `0.0.0.0:8000` (accessible from any computer, smartphone, or tablet on your network).
> 7. Automatically launches the platform in your default web browser!

---

### 🍎 macOS & 🐧 Linux
Open Terminal in the project folder and run:
```bash
chmod +x Launch-Arohan.sh run.sh
./Launch-Arohan.sh
# or simply:
./run.sh
```

---

### 📱 Accessing from Mobile Phones, Tablets & Other Laptops
When the server starts, it prints the local network URL in the console. Any device connected to the **same campus Wi-Fi or LAN** can access the full platform directly:

```
[🖥️ LOCAL COMPUTER]
-> http://localhost:8000

[📱 ANY DEVICE ON CAMPUS WI-FI / LAN (Smartphones, iPads, Android Tablets, Laptops)]
-> http://<YOUR_LOCAL_IP>:8000  (e.g., http://192.168.1.50:8000 or http://10.1.65.29:8000)
```

No software or apps need to be installed on student or faculty mobile devices — simply open Chrome, Safari, Firefox, or Edge on the phone or tablet!

---

## 🔑 Default Demo Login Accounts

Quickly test each user persona using the pre-seeded credentials:

| Role | Email | Password | Primary Features |
| :--- | :--- | :--- | :--- |
| **🎓 Student** | `student1@imrd.ac.in` | `Student@123` | Dashboard, Bayesian Mastery, MCAT Assessments, Curriculum |
| **👨‍🏫 Faculty** | `faculty1@imrd.ac.in` | `Faculty@123` | Class Performance, Interventions, Remediation Plan, Rubrics |
| **🛡️ Exam Controller** | `controller@imrd.ac.in` | `Exam@123` | Real-time Proctored Exam Monitoring, Integrity Log, Exam Lockout |
| **⚙️ Admin** | `admin@imrd.ac.in` | `Admin@123` | Authorized User Management, Security Hardening, Audit Logs |

> **Note:** A 1-click **Role Switcher** is also available at the bottom-left of the sidebar in development mode for rapid switching between roles.

---

## 📋 System Prerequisites

| Component | Minimum Version | Requirement |
| :--- | :--- | :--- |
| **Python** | 3.10 or higher | Required on the server host machine. Ensure **"Add python.exe to PATH"** is checked. |
| **Node.js** | 18+ *(Optional)* | **Not required to run the app.** The frontend distribution (`frontend/dist`) is pre-compiled. Node.js is only needed if you edit frontend source code. |
| **Database** | SQLite WAL | Embedded asynchronous SQLite (`isdp_campus.db`). Zero external database installation needed! |

---

## 🛠️ Developer & Advanced Commands

### Rebuilding Frontend (if source code is modified)
```bash
cd frontend
npm install
npm run build
```

### Running Backend Tests
```bash
python -m pytest backend/tests/ -v
```

### Interactive API Documentation
Once the server is running, explore the interactive Swagger and ReDoc documentation:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

---

## 🏛️ Institution & Copyright
- **Institution:** RC Patel Educational Trust's Institute of Management Research and Development (IMRD), Shirpur
- **Project:** Arohan ISDP — Institutional Student Development Platform
- **Tagline:** Ideas Today • Impact Tomorrow
