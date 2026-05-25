#!/bin/bash
# =============================================================================
# BROCKSTON Studio — Single-command launcher
# Starts: UltimateEV (5174) → Brockston educator (7777) → IDE Board (5055)
# Requires: Ollama running on 11434 with llama3.2 and qwen2.5-coder:32b pulled
# Stops cleanly on Ctrl+C.
# =============================================================================

set -u  # error on undefined vars (but NOT -e — we want partial-failure to keep running)

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

ULTIMATEEV_LOG="$LOG_DIR/ultimateev.log"
BROCKSTON_LOG="$LOG_DIR/brockston.log"
IDE_LOG="$LOG_DIR/ide.log"

# ----- defaults (overridable via .env or shell) ------------------------------
[ -f .env ] && set -a && source .env && set +a

export BROCKSTON_HOST="${BROCKSTON_HOST:-127.0.0.1}"
export BROCKSTON_PORT="${BROCKSTON_PORT:-7777}"          # Brockston educator backend
export IDE_PORT="${IDE_PORT:-5055}"                       # IDE Board frontend (main.py)
export ULTIMATEEV_PORT="${ULTIMATEEV_PORT:-5174}"         # UltimateEV node server
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-coder:32b}"
export LLM_MODEL_GENERAL="${LLM_MODEL_GENERAL:-qwen2.5-coder:32b}"
export LLM_MODEL_CODER="${LLM_MODEL_CODER:-qwen2.5-coder:32b}"
export LLM_MODEL="${LLM_MODEL:-$LLM_MODEL_GENERAL}"

PIDS=()

# ----- colors ----------------------------------------------------------------
C_RESET=$'\033[0m'
C_DIM=$'\033[2m'
C_BOLD=$'\033[1m'
C_GREEN=$'\033[32m'
C_YELLOW=$'\033[33m'
C_RED=$'\033[31m'
C_CYAN=$'\033[36m'

banner() {
    echo ""
    echo "${C_BOLD}=========================================${C_RESET}"
    echo "${C_BOLD}  BROCKSTON Studio${C_RESET}"
    echo "${C_DIM}  The Christman AI Project${C_RESET}"
    echo "${C_BOLD}=========================================${C_RESET}"
    echo ""
}

info()  { echo "${C_CYAN}[info]${C_RESET} $*"; }
ok()    { echo "${C_GREEN}[ ok ]${C_RESET} $*"; }
warn()  { echo "${C_YELLOW}[warn]${C_RESET} $*"; }
fail()  { echo "${C_RED}[fail]${C_RESET} $*"; }

# ----- preflight -------------------------------------------------------------
preflight() {
    info "Preflight..."

    command -v python3 >/dev/null 2>&1 || { fail "python3 not installed"; exit 1; }
    command -v node    >/dev/null 2>&1 || { fail "node not installed";    exit 1; }
    command -v curl    >/dev/null 2>&1 || warn "curl missing — health checks limited"

    # FastAPI/uvicorn check
    if ! python3 -c "import fastapi, uvicorn" >/dev/null 2>&1; then
        warn "fastapi/uvicorn not installed — running 'pip install -r requirements.txt'"
        pip install -r requirements.txt || { fail "pip install failed"; exit 1; }
    fi

    # node_modules check
    if [ ! -d "$ROOT/node_modules/express" ]; then
        warn "node_modules/express missing — running 'npm install'"
        ( cd "$ROOT" && npm install ) || { fail "npm install failed"; exit 1; }
    fi

    # Ollama reachable?
    if curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; then
        ok "Ollama reachable at $OLLAMA_BASE_URL"
    else
        warn "Ollama not reachable at $OLLAMA_BASE_URL — start it with 'ollama serve' in another terminal"
        warn "Brockston and UltimateEV will start but won't answer until Ollama is up"
    fi

    ok "Preflight complete"
}

# ----- port check ------------------------------------------------------------
port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    else
        # fallback for systems without lsof
        (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
    fi
}

check_ports() {
    local conflict=0
    for p in "$ULTIMATEEV_PORT" "$BROCKSTON_PORT" "$IDE_PORT"; do
        if port_in_use "$p"; then
            fail "Port $p already in use"
            conflict=1
        fi
    done
    [ "$conflict" = "1" ] && { fail "Free the ports above and try again."; exit 1; }
    ok "Ports $ULTIMATEEV_PORT, $BROCKSTON_PORT, $IDE_PORT are free"
}

# ----- shutdown handler ------------------------------------------------------
shutdown() {
    echo ""
    info "Shutting down..."
    for pid in "${PIDS[@]:-}"; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null
    done
    # Give them a moment, then SIGKILL anything stubborn
    sleep 1
    for pid in "${PIDS[@]:-}"; do
        [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
    done
    ok "All processes stopped"
    exit 0
}
trap shutdown INT TERM

# ----- start each element ----------------------------------------------------
start_ultimateev() {
    info "Starting UltimateEV (port $ULTIMATEEV_PORT)..."
    PORT="$ULTIMATEEV_PORT" OLLAMA_MODEL="$OLLAMA_MODEL" \
        node ultimateev_server.js >"$ULTIMATEEV_LOG" 2>&1 &
    PIDS+=($!)
    sleep 1
}

start_brockston() {
    info "Starting Brockston educator backend (port $BROCKSTON_PORT)..."
    BROCKSTON_HOST="$BROCKSTON_HOST" BROCKSTON_PORT="$BROCKSTON_PORT" \
        python3 -m uvicorn backend.launcher:app \
            --host "$BROCKSTON_HOST" --port "$BROCKSTON_PORT" \
            >"$BROCKSTON_LOG" 2>&1 &
    PIDS+=($!)
    sleep 1
}

start_ide() {
    info "Starting IDE Board (port $IDE_PORT)..."
    python3 -m uvicorn main:app --host "$BROCKSTON_HOST" --port "$IDE_PORT" \
        >"$IDE_LOG" 2>&1 &
    PIDS+=($!)
    sleep 1
}

# ----- post-start health checks ----------------------------------------------
wait_ready() {
    local url="$1"
    local label="$2"
    local tries=20
    while [ $tries -gt 0 ]; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            ok "$label is responding"
            return 0
        fi
        tries=$((tries-1))
        sleep 0.5
    done
    warn "$label not responding yet — check ${LOG_DIR}/$(echo "$label" | tr 'A-Z ' 'a-z_').log"
    return 1
}

# =============================================================================
# Main
# =============================================================================
banner
preflight
check_ports
start_ultimateev
start_brockston
start_ide

echo ""
info "Health checks..."
wait_ready "http://127.0.0.1:$ULTIMATEEV_PORT/health" "UltimateEV"  || true
wait_ready "http://127.0.0.1:$BROCKSTON_PORT/api/health" "Brockston" || \
wait_ready "http://127.0.0.1:$BROCKSTON_PORT/health" "Brockston"     || true
wait_ready "http://127.0.0.1:$IDE_PORT/api/health" "IDE"             || \
wait_ready "http://127.0.0.1:$IDE_PORT/" "IDE"                       || true

echo ""
echo "${C_BOLD}=========================================${C_RESET}"
ok "BROCKSTON Studio is up."
echo ""
echo "  IDE Board     ${C_CYAN}http://localhost:$IDE_PORT${C_RESET}"
echo "  Brockston     ${C_DIM}http://localhost:$BROCKSTON_PORT${C_RESET}"
echo "  UltimateEV    ${C_DIM}http://localhost:$ULTIMATEEV_PORT${C_RESET}"
echo "  Ollama        ${C_DIM}$OLLAMA_BASE_URL${C_RESET}"
echo ""
echo "  Logs:         ${C_DIM}$LOG_DIR/${C_RESET}"
echo "  Stop:         ${C_DIM}Ctrl+C${C_RESET}"
echo "${C_BOLD}=========================================${C_RESET}"
echo ""
info "Tailing all three logs (Ctrl+C to stop everything)..."
echo ""

# Tail all logs together until shutdown (portable: works on macOS bash 3.2)
tail -F "$ULTIMATEEV_LOG" "$BROCKSTON_LOG" "$IDE_LOG" 2>/dev/null &
TAIL_PID=$!

# Wait for any backend to exit unexpectedly
wait
shutdown
