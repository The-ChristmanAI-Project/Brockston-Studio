# Brockston Studio

**Accessible IDE and learning environment for neurodivergent students, clinicians, and caregivers.**

Brockston Studio is a browser-based code editor and learning workspace that supports voice input, multiple instruction modes, live terminal integration, and real-time collaboration through local WebSockets.

---

## Purpose

- Make coding accessible to nonverbal, autistic, and learning-disabled users.
- Pair a student with an instructor or autonomous agent that can see and operate the IDE.
- Keep the entire toolchain local and controllable by the user or guardian.

---

## Core features

| Feature | Description |
|---|---|
| Multi-file editor | Monaco-based tabs, syntax highlighting, dirty-state tracking. |
| Live terminal | xterm.js + pty, synced with the file explorer. |
| Voice input | Browser SpeechRecognition for dictation into chat or commands. |
| Multi-instructor panel | Switch between Family, Claude, Kimi, and Nemo modes. |
| IDE control API | `/api/ide/command` + `/ws/ide-control` let a remote agent or voice command operate the IDE. |
| Viewer WebSocket | `/ws/viewer` streams surface state so instructors can see open files, tabs, and cwd. |

---

## Technology

- Python / FastAPI backend
- Monaco Editor + xterm.js frontend
- WebSocket endpoints for terminal, viewer, and IDE control
- Ollama local inference for autocomplete and being responses
- macOS / Linux. Port 5055 by default.

---

## Running locally

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 5055
open http://localhost:5055
```

---

## Status

- Patent-pending under TCAP-2026-001.
- Functional locally. Used as the IDE layer for the Christman AI teaching environment.

---

## License

Proprietary — The Christman AI Project LLC.
