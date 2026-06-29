#!/bin/bash
# Wire Brockston-Studio IDE board to tcap-compute (voice + studio bridge division).
# Called from start.sh after IDE health check, or standalone after ./start.sh.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[ -f .env ] && set -a && source .env && set +a

TCAP_COMPUTE_ENABLED="${TCAP_COMPUTE_ENABLED:-1}"
if [ "$TCAP_COMPUTE_ENABLED" = "0" ]; then
    echo "[compute] Disabled (TCAP_COMPUTE_ENABLED=0)"
    exit 0
fi

TCAP_ROOT="${TCAP_COMPUTE_ROOT:-$HOME/tcap-compute}"
IDE_URL="${STUDIO_IDE_URL:-http://127.0.0.1:${IDE_PORT:-5055}}"
BRIDGE_URL="${CHRISTMAN_BRIDGE_URL:-http://127.0.0.1:8765}"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

VENV_PYTHON="$ROOT/backend/venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "[compute] backend/venv missing — run ./start.sh first"
    exit 1
fi

if [ ! -d "$TCAP_ROOT/tcap_compute" ]; then
    echo "[compute] tcap-compute not found at $TCAP_ROOT"
    exit 1
fi

"$VENV_PYTHON" -c "import websockets" 2>/dev/null || \
    "$VENV_PYTHON" -m pip install -q websockets

export TCAP_COMPUTE_ROOT="$TCAP_ROOT"
export STUDIO_IDE_URL="$IDE_URL"
export CHRISTMAN_BRIDGE_URL="$BRIDGE_URL"
export PYTHONPATH="$TCAP_ROOT${PYTHONPATH:+:$PYTHONPATH}"

is_running() {
    pgrep -f "$1" >/dev/null 2>&1
}

wait_url() {
    local url="$1"
    local label="$2"
    local tries="${3:-30}"
    while [ $tries -gt 0 ]; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "[compute] $label ok"
            return 0
        fi
        tries=$((tries - 1))
        sleep 1
    done
    echo "[compute] WARN: $label not responding at $url"
    return 1
}

# Bridge (voice source) — start only if down
if ! curl -fsS "$BRIDGE_URL/health" >/dev/null 2>&1; then
    BRIDGE_ROOT="${CHRISTMAN_BRIDGE_ROOT:-$HOME/mcp-media-ingestor}"
    if [ -f "$BRIDGE_ROOT/main.py" ]; then
        echo "[compute] Starting Christman Bridge..."
        rm -f "$HOME/Library/Logs/christman_bridge.lock" 2>/dev/null || true
        UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"
        if [ -x "$UV_BIN" ]; then
            (cd "$BRIDGE_ROOT" && nohup "$UV_BIN" run python main.py >>"$LOG_DIR/bridge.log" 2>&1 &)
        else
            (cd "$BRIDGE_ROOT" && nohup "$BRIDGE_ROOT/.venv/bin/python3" main.py >>"$LOG_DIR/bridge.log" 2>&1 &)
        fi
        wait_url "$BRIDGE_URL/health" "Christman Bridge" 12 || true
    else
        echo "[compute] WARN: Bridge not found at $BRIDGE_ROOT"
    fi
fi

# Voice loop — bridge → IDE
if ! is_running "tcap_compute.voice_loop"; then
    echo "[compute] Starting voice loop (bridge → IDE)..."
    nohup "$VENV_PYTHON" -m tcap_compute.voice_loop >>"$LOG_DIR/voice-loop.log" 2>&1 &
fi

# Studio division — bridge WS → IDE executor
if ! is_running "tcap_compute studio"; then
    echo "[compute] Starting studio division (bridge WS → IDE)..."
    nohup "$VENV_PYTHON" -m tcap_compute studio >>"$LOG_DIR/studio-division.log" 2>&1 &
fi

wait_url "$IDE_URL/api/health" "Studio IDE" || true
echo "[compute] IDE board wired — voice + studio division → $IDE_URL"