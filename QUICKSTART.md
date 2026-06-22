# BROCKSTON Studio — Quick Start

One command. Three elements. Get to work.

---

## Prerequisites

You need **Ollama** running with two models pulled:

```bash
ollama serve                          # in its own terminal
ollama pull llama3.2                  # for UltimateEV (default)
ollama pull qwen2.5-coder:32b         # for Brockston code questions
```

You also need **Python 3.10+** and **Node 18+**.

---

## Install

```bash
pip install -r requirements.txt
npm install
```

`start.sh` will also auto-install on first run if anything is missing.

---

## Launch (one command)

```bash
./start.sh
```

That single command brings up all three elements:

| Element        | Port  | What it does                                |
|----------------|-------|---------------------------------------------|
| IDE Board      | 5055  | Monaco editor, chat panel, terminal         |
| Brockston      | 9001  | Educator backend (chat, file ops, suggest)  |
| UltimateEV     | 5174  | Code Mechanic (handles code questions first)|
| Ollama         | 11434 | Local LLM host                              |

When health checks pass, open **http://localhost:5055** in your browser.

Press **Ctrl+C** to stop everything cleanly.

Logs land in `./logs/` — `ultimateev.log`, `brockston.log`, `ide.log`.

---

## Run individual elements (advanced)

If you want each one in its own terminal:

```bash
# Terminal 1
node ultimateev_server.js                                     # port 5174

# Terminal 2
python -m uvicorn backend.launcher:app --port 9001            # port 9001

# Terminal 3
python -m uvicorn main:app --host 127.0.0.1 --port 5055       # port 5055
```

---

## Environment (optional)

`.env` at the repo root, or export inline. The launcher reads these:

| Variable             | Default                       | Purpose                                |
|----------------------|-------------------------------|----------------------------------------|
| `BROCKSTON_HOST`     | `127.0.0.1`                   | bind address                           |
| `BROCKSTON_PORT`     | `9001`                        | Brockston educator port                |
| `IDE_PORT`           | `5055`                        | IDE Board port                         |
| `ULTIMATEEV_PORT`    | `5174`                        | UltimateEV port                        |
| `OLLAMA_BASE_URL`    | `http://127.0.0.1:11434`      | where Ollama lives                     |
| `OLLAMA_MODEL`       | `llama3.2`                    | UltimateEV's default model             |
| `LLM_MODEL_CODER`    | `qwen2.5-coder:32b`           | Brockston's coder model                |
| `ANTHROPIC_API_KEY`  | —                             | enables Claude features                |
| `BROCKSTON_WORKSPACE`| repo root                     | where your code lives                  |

---

## First-run sanity check

1. Open **http://localhost:5055**.
2. Type a file path in the top bar (e.g. `README.md`) → **Open**.
3. Ask Brockston a question: "Explain what this code does."
4. Switch to the **UltimateEV** tab for code-mechanic questions.
5. Save with **Ctrl+S** / **Cmd+S**.

---

## Troubleshooting

**"Port already in use"** — Something is holding 5055, 7777, or 5174. Free it (or change the port via env var) and run `./start.sh` again.

**"Ollama not reachable"** — Start it in another terminal: `ollama serve`. Brockston and UltimateEV will start but won't answer until Ollama is up.

**"Failed to communicate with BROCKSTON"** — Check `logs/brockston.log` for the real error.

**Monaco editor blank** — The CDN can be blocked on some networks. Check the browser console.

**Path is outside workspace root** — Set `BROCKSTON_WORKSPACE` to a directory that contains the file, or use a path inside the repo.

---

Full architecture, voice pipeline, and being roster live in [README.md](README.md).
