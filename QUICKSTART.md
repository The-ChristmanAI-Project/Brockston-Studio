# Brockston-Studio — Quick Start

One command after clone. Three services. Open the board.

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.10+** | `python3 --version` |
| **Node 18+** | `node --version` |
| **Ollama** | [ollama.com](https://ollama.com) — local LLM host |

---

## 2. Clone and launch

```bash
git clone https://github.com/The-ChristmanAI-Project/Brockston-Studio.git
cd Brockston-Studio
chmod +x start.sh
```

**Terminal A — Ollama (keep running):**
```bash
ollama serve
```

**Terminal B — models (once per machine):**
```bash
ollama pull llama3.2                  # chat / vocal / fast path
ollama pull qwen2.5-coder:32b         # code / tools / UltimateEV
```

**Low-RAM machine?** Use a smaller coder model in `.env` after first run:
```bash
LLM_MODEL_CODER=qwen2.5-coder:7b
BEING_AGENT_MODEL=qwen2.5-coder:7b
```
Then `ollama pull qwen2.5-coder:7b`

**Terminal B — start the stack:**
```bash
./start.sh
```

First run automatically:
1. Creates `.env` from `.env.example` (if missing)
2. Creates `backend/venv` and `pip install -r requirements.txt`
3. Runs `npm install` only if `node_modules` is missing

When you see `Brockston-Studio is up`, open **http://localhost:5055**.

**Ctrl+C** stops all three services cleanly.

---

## 3. What runs

| Element | Port | Role |
|---------|------|------|
| **Studio IDE** | 5055 | Browser IDE — editor, terminal, beings panel |
| **Studio backend** | 9003 | Educator API in this repo — chat, suggest-fix |
| **UltimateEV** | 5174 | Code mechanic — heavy code questions |
| **Ollama** | 11434 | Local models (you run separately) |

Logs: `./logs/ultimateev.log`, `./logs/studio-backend.log`, `./logs/ide.log`

---

## 4. Configure (optional)

Edit `.env` at the repo root:

| Variable | Default | Purpose |
|----------|---------|---------|
| `STUDIO_WORKSPACE` | `~/Code` | Studio IDE default folder (last path remembered in browser) |
| `LLM_MODEL_GENERAL` | `llama3.2` | Fast chat for The Family |
| `LLM_MODEL_CODER` | `qwen2.5-coder:32b` | Code / tools / UltimateEV |
| `STUDIO_BACKEND_PORT` | `9003` | Studio educator backend port |
| `IDE_PORT` | `5055` | Studio IDE port |
| `ANTHROPIC_API_KEY` | *(empty)* | Enables Claude instructor (optional) |

Restart `./start.sh` after changing `.env`.

Verify wiring:
```bash
curl -s http://localhost:5055/api/health | python3 -m json.tool
```

---

## 5. First-run sanity check

1. Open **http://localhost:5055** — explorer should show `~/Code` (or your `STUDIO_WORKSPACE`).
2. Click a folder or file — terminal `cd` should follow.
3. Ask **Family**: "What is a variable?" — should answer via local Ollama.
4. Ask a code question — may route to tool loop or coder model (slower on first hit).
5. **Cmd+S** saves the open file.

---

## 6. Run services individually (advanced)

```bash
source backend/venv/bin/activate

# Terminal 1
node ultimateev_server.js

# Terminal 2
python -m uvicorn backend.launcher:app --host 127.0.0.1 --port 9003

# Terminal 3
python -m uvicorn main:app --host 127.0.0.1 --port 5055
```

---

## 7. Troubleshooting

**`Port already in use`** — Something holds 5055, 9003, or 5174. `lsof -iTCP:5055 -sTCP:LISTEN` then kill, or change ports in `.env`.

**`python3 -m venv failed`** — Install Python 3.10+ from python.org or Homebrew.

**`Ollama not reachable`** — Run `ollama serve`. IDE starts but beings stay silent until Ollama is up.

**`Model X not pulled`** — `ollama pull <model>` for each name in `.env`.

**Monaco editor blank** — CDN blocked on your network; check browser console.

**Beings reference skills paths that don't exist** — Normal on a fresh install. Beings still work; optional Grok/Cursor skill folders are Everett's local tooling, not required for the IDE.

---

Architecture and feature list: [README.md](README.md)