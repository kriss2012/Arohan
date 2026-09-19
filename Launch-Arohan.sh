#!/usr/bin/env bash
# ======================================================================
#   AROHAN ISDP — INSTITUTIONAL CAMPUS LMS LAUNCHER (macOS & Linux)
#   RC Patel Educational Trust's IMRD, Shirpur
# ======================================================================

set -e

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "  AROHAN ISDP — INSTITUTIONAL CAMPUS LMS LAUNCHER"
echo "  RC Patel Educational Trust's IMRD, Shirpur"
echo "======================================================================"
echo ""

# 1. Detect Python 3
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3 was not detected on this system!"
    echo "Please install Python 3 (version 3.10 or higher) using your package manager:"
    echo "  macOS (Homebrew): brew install python"
    echo "  Ubuntu / Debian : sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    echo "  Arch Linux      : sudo pacman -S python python-pip"
    echo "  Fedora          : sudo dnf install python3 python3-pip"
    exit 1
fi

echo "[OK] Detected Python runtime: $($PYTHON_CMD --version)"

# 2. Setup Virtual Environment
PYTHON_EXEC="$PYTHON_CMD"
if [ -f ".venv/bin/python" ]; then
    echo "[OK] Using existing virtual environment at .venv"
    PYTHON_EXEC=".venv/bin/python"
else
    echo "[INFO] Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv 2>/dev/null || true
    if [ -f ".venv/bin/python" ]; then
        echo "[OK] Virtual environment created successfully."
        PYTHON_EXEC=".venv/bin/python"
    else
        echo "[WARN] Could not create .venv. Falling back to system Python."
    fi
fi

# 3. Check and Install Dependencies
echo "[INFO] Checking Python packages..."
if ! "$PYTHON_EXEC" -c "import fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, pydantic_settings, jwt, bcrypt, httpx" 2>/dev/null; then
    echo ""
    echo "======================================================================"
    echo "  DOWNLOADING AND INSTALLING REQUIRED PACKAGES..."
    echo "  This happens only on first run. Please wait a moment."
    echo "======================================================================"
    "$PYTHON_EXEC" -m pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        "$PYTHON_EXEC" -m pip install -r requirements.txt
    else
        "$PYTHON_EXEC" -m pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic pydantic-settings email-validator python-multipart PyJWT bcrypt httpx pytest pytest-asyncio
    fi
    echo "[OK] All dependencies successfully installed."
else
    echo "[OK] All Python requirements are satisfied."
fi

# 4. Ensure Local Storage Directories
mkdir -p local_storage/assignments
mkdir -p local_storage/submissions
mkdir -p local_storage/resources
mkdir -p local_storage/backups
mkdir -p local_storage/temp
mkdir -p local_storage/logs

# 5. Check Frontend Dist
if [ ! -f "frontend/dist/index.html" ]; then
    if command -v npm >/dev/null 2>&1; then
        echo "[INFO] Building frontend distribution package..."
        (cd frontend && npm install && npm run build)
    else
        echo "[WARN] frontend/dist/index.html is missing and npm was not found."
    fi
fi

# 6. Launch Server
echo ""
echo "======================================================================"
echo "  STARTING AROHAN ISDP SERVER..."
echo "======================================================================"
exec "$PYTHON_EXEC" start_server.py
