# Brockston Studio

**Accessible IDE and learning environment for neurodivergent students, clinicians, and caregivers.**

Browser-based code editor with voice input, live terminal, multiple AI instructors, and local Ollama inference. Part of [The Christman AI Project](https://github.com/EverettNC/Brockston-Studio).

---

## Quick start (GitHub download)

**Prerequisites:** macOS or Linux · Python 3.10+ · Node 18+ · [Ollama](https://ollama.com)

```bash
git clone https://github.com/EverettNC/Brockston-Studio.git
cd Brockston-Studio
chmod +x start.sh

# Terminal 1 — Ollama (leave running)
ollama serve

# Terminal 2 — pull models once (32B is heavy; see QUICKSTART for lighter options)
ollama pull llama3.2
ollama pull qwen2.5-coder:32b

# Terminal 2 — launch everything
./start.sh
```

Open **http://localhost:5055**

On first run, `start.sh` will:
- Copy `.env.example` → `.env` if you don't have one
- Create `backend/venv` and install Python deps (not shipped in git)
- Run `npm install` only if Node deps are missing
- Start IDE (5055), Brockston educator (9003), and UltimateEV (5174)

Press **Ctrl+C** to stop all three services.

Full details: **[QUICKSTART.md](QUICKSTART.md)**

---

## What you get

| Feature | Description |
|---------|-------------|
| Multi-file editor | Monaco tabs, syntax highlighting, save to disk |
| Live terminal | xterm.js synced with the file explorer (`cd` follows) |
| Voice input | Browser speech recognition into chat |
| Instructors | Family (Ollama), Nemo, Kimi (optional NVIDIA key), Claude (optional) |
| Being Eyes | Beings can `ls` / `read` / `patch` / `run` on your machine |
| IDE control | `/ws/ide-control` — remote agent can open files, run terminal commands |

**Default folder:** `~/Code` (set `BROCKSTON_WORKSPACE` in `.env`). The browser remembers your last-opened folder.

**Model split (local Ollama):**
- `llama3.2` — fast chat, vocal, Nemo partner mode
- `qwen2.5-coder:32b` — code, tools, UltimateEV, suggest-fix

---

## Ports

| Service | Port | URL |
|---------|------|-----|
| IDE Board | 5055 | http://localhost:5055 |
| Brockston educator | 9003 | http://localhost:9003 |
| UltimateEV | 5174 | http://localhost:5174 |
| Ollama | 11434 | http://127.0.0.1:11434 |

Check wiring: `curl http://localhost:5055/api/health`

---

## Optional API keys (`.env`)

| Key | Enables |
|-----|---------|
| *(none)* | Full local IDE + Ollama beings |
| `NVIDIA_API_KEY` | Kimi K2.6 tutor in the beings panel |
| `ANTHROPIC_API_KEY` | Claude instructor |
| `GITHUB_TOKEN` | Clone private repos from the IDE |

Never commit `.env` — it is gitignored.

---

## Project layout

```
Brockston-Studio/
├── start.sh              # One-command launcher
├── main.py               # IDE server (port 5055)
├── backend/              # Beings, eyes, speech, launcher
├── frontend/index.html   # Browser IDE (Monaco + xterm)
├── ultimateev_server.js  # Code mechanic (port 5174)
├── .env.example          # Copy to .env on first run
└── requirements.txt      # Python deps (installed into backend/venv)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `backend/venv/bin/python` missing | Run `./start.sh` — it creates the venv automatically |
| Port already in use | Free 5055 / 9003 / 5174 or change ports in `.env` |
| Ollama not reachable | `ollama serve` in another terminal |
| Beings don't answer | `ollama pull llama3.2` (and coder model in `.env`) |
| Opens wrong folder | Set `BROCKSTON_WORKSPACE=~/Code` in `.env`, restart |

Logs: `./logs/ide.log`, `./logs/brockston.log`, `./logs/ultimateev.log`

---

## Status

Patent-pending (TCAP-2026-001). Functional locally. Used as the IDE layer for the Christman AI teaching environment.

## License

Proprietary — The Christman AI Project LLC.