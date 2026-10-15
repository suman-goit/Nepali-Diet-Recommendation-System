#!/usr/bin/env bash
# Nepali Diet Recommendation System - One-Click Launcher (Linux / macOS)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Locate Python in virtual environment or fallback to system python3
VENV_PYTHON=""
if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
elif [ -f "$BACKEND_DIR/venv/bin/python" ]; then
    VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
elif [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
elif command -v python3 &>/dev/null; then
    VENV_PYTHON="python3"
elif command -v python &>/dev/null; then
    VENV_PYTHON="python"
else
    echo "Error: Python is not installed or not in PATH."
    exit 1
fi

echo "=========================================================="
echo "  Starting Nepali Diet Recommendation System (DFTQC 2012) "
echo "=========================================================="
echo "Using Python: $VENV_PYTHON"

# Ensure frontend dependencies are installed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "[*] Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
fi

echo "[1/4] Running backend database migrations..."
"$VENV_PYTHON" "$BACKEND_DIR/manage.py" migrate

echo "[2/4] Seeding Nepali food database..."
"$VENV_PYTHON" "$BACKEND_DIR/manage.py" seed_data

echo "[3/4] Training Decision Tree model..."
"$VENV_PYTHON" "$BACKEND_DIR/manage.py" train_decision_tree

echo "[4/4] Launching Backend on http://127.0.0.1:8000 and Frontend on http://localhost:5173..."

cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

"$VENV_PYTHON" "$BACKEND_DIR/manage.py" runserver 8000 &
BACKEND_PID=$!

(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

wait

