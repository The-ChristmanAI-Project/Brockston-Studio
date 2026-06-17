import os
import subprocess
import pty
import select
import json
import logging
import asyncio
from pathlib import Path
import fastapi # pyright: ignore[reportMissingImports]
import fastapi.middleware.cors # pyright: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles # pyright: ignore[reportMissingImports]
from fastapi.responses import HTMLResponse, FileResponse, Response # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]

try:
    from backend.ai_client import get_ai_response
except ImportError:
    get_ai_response = None

try:
    from backend.speech_service import SpeechService
except ImportError:
    SpeechService = None

# Logger must exist regardless of whether SpeechService imported.
# (Previously this was nested inside the except block above, so when
# SpeechService imported cleanly `logger` was never defined and every
# endpoint that called logger.info crashed with NameError.)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrockstonStudio")

app = fastapi.FastAPI()

origins = ["*"]

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Claude as additional instructor
# MUST be after app = FastAPI() and logger setup
try:
    from backend.claude_router import router as claude_router
    app.include_router(claude_router)
    logger.info("Claude router mounted — additional instructor available at /api/claude")
except Exception as e:
    logger.warning(f"Claude router not available: {e}")

# Perplexity Sonar — already linked via PERPLEXITY_API_KEY, expose as selectable instructor
try:
    from backend.perplexity_service import PerplexityService
    _perplexity_svc = PerplexityService()
    if not _perplexity_svc.is_available:
        _perplexity_svc = None
        logger.warning("Perplexity linked but not available (check key)")
    else:
        logger.info("Perplexity Sonar linked and ready as additional instructor")
except Exception as e:
    _perplexity_svc = None
    logger.warning(f"Perplexity service not available: {e}")

class ChatRequest(BaseModel):
    message: str

@app.get("/api/health")
async def health_check():
    return {"status": "10 Toes Down", "system": "Online"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Routes to UltimateEV first, falls back to Ollama/Brockston."""
    import httpx
    try:
        logger.info(f"Trying UltimateEV: {request.message}")
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "http://localhost:5174/api/translate",
                json={"message": request.message}
            )
            data = response.json()
            return {"response": f"[ULTIMATE_EV]: {data['response']}"}
            
    except Exception as e:
        logger.warning(f"UltimateEV offline, falling back to local AI: {e}")
        try:
            response_text = get_ai_response(request.message)
            return {"response": response_text}
        except Exception as inner_e:
            raise fastapi.HTTPException(status_code=500, detail=str(inner_e))

# Perplexity as additional instructor (search-grounded, cited answers)
# Since Perplexity is already "linked", this exposes it in the board UI
@app.post("/api/perplexity")
async def perplexity_endpoint(request: ChatRequest):
    """Direct access to Perplexity Sonar for live search / research queries."""
    if not _perplexity_svc:
        raise fastapi.HTTPException(status_code=500, detail="Perplexity not available (PERPLEXITY_API_KEY)")

    try:
        # The rich context (file + selection) is already baked into the message by the frontend
        result = _perplexity_svc.generate_content(
            request.message,
            max_tokens=1500,
            recency_filter="month"  # recent info by default
        )
        return {"response": f"[PERPLEXITY]: {result}"}
    except Exception as e:
        logger.error(f"Perplexity error: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

# ==========================================
# AUDIO ROUTE (This makes the kids' TTS work)
# ==========================================
@app.post("/api/speech/synthesize")
async def synthesize_speech_route(request: fastapi.Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        # Voice ID for local synthesis
        voice = data.get("voice", "default") 
        
        speech_svc = SpeechService()
        audio_bytes = await speech_svc.synthesize_speech(text=text, voice_id=voice)
        
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Speech Synthesis Error: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ==========================================
# AUDIO PLAYER ROUTE - For students to play their old school rock and Soul Train
# ==========================================
@app.get("/api/audio")
async def get_audio(filename: str):
    """Serve audio files (mp3, wav, etc.) from anywhere in the user's home for the music player.
    Lets senior students (and everyone) play their own old school rock and Soul Train tracks
    right inside the IDE while coding and talking to the beings.
    """
    try:
        target = _resolve_user_path(filename, WORKSPACE_ROOT)
        if not target.exists() or not target.is_file():
            raise fastapi.HTTPException(status_code=404, detail="Audio file not found")

        ext = target.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".aac": "audio/aac",
        }
        media_type = mime_types.get(ext, "audio/mpeg")

        with open(target, "rb") as f:
            content = f.read()

        logger.info(f"Playing audio: {target}")
        return Response(content=content, media_type=media_type)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio Playback Error: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# File operations
#
# The IDE is allowed to read/list/write anywhere inside the user's HOME
# directory. "workspace" is the starting point, not a cage — when the user
# cd's into another project (AlphaVox, AlphaWolf, etc.), the explorer should
# follow them there. The HOME guard prevents path traversal into system files
# like /etc/passwd while keeping every real project reachable.
# ----------------------------------------------------------------------------
USER_HOME = Path(os.path.expanduser("~")).resolve()
WORKSPACE_ROOT = Path(".").resolve()

def _resolve_user_path(raw: str, default: Path) -> Path:
    """Resolve a path argument from the client.

    Rules:
      - Empty string -> `default` (usually workspace root)
      - Absolute path -> used as-is
      - Relative path -> resolved against the workspace root
      - Resolved path must live inside the user's HOME (security boundary)
      - '..' segments in the *input* are rejected as a defense-in-depth check
    """
    if not raw:
        return default
    # Reject literal traversal attempts in the raw input.
    parts = raw.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise fastapi.HTTPException(status_code=400, detail="Path contains '..'")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = WORKSPACE_ROOT / candidate
    resolved = candidate.resolve()
    # Stay inside the user's home tree.
    try:
        resolved.relative_to(USER_HOME)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Path outside user home ({USER_HOME})",
        )
    return resolved


@app.get("/api/files")
async def list_files(path: str = ""):
    try:
        target = _resolve_user_path(path, WORKSPACE_ROOT)
        if not target.exists():
            raise fastapi.HTTPException(status_code=404, detail="Directory not found")
        if not target.is_dir():
            raise fastapi.HTTPException(status_code=400, detail="Not a directory")
        files = []
        for item in sorted(os.listdir(target)):
            if item.startswith(".") or item.startswith("__"):
                continue
            full_path = target / item
            try:
                if full_path.is_dir():
                    files.append({"name": item, "type": "folder"})
                elif full_path.is_file():
                    files.append({"name": item, "type": "file"})
            except (PermissionError, OSError):
                continue
        # Sort: folders first, then files, both alphabetically
        files.sort(key=lambda f: (f["type"] != "folder", f["name"].lower()))
        return {
            "files": files,
            "path": str(target),
            "is_workspace": str(target) == str(WORKSPACE_ROOT),
            "home": str(USER_HOME),
        }
    except fastapi.HTTPException:
        raise
    except Exception as e:
        logger.error(f"File Listing Error: {e}")
        return {"files": [], "path": path, "error": str(e)}

@app.get("/api/read_file")
async def read_file(filename: str):
    try:
        target = _resolve_user_path(filename, WORKSPACE_ROOT)
        if not target.exists() or not target.is_file():
            raise fastapi.HTTPException(status_code=404, detail="File not found")
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "filename": str(target)}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise fastapi.HTTPException(status_code=404, detail=f"Cannot read file: {e}")

class WriteFileRequest(BaseModel):
    filename: str
    content: str

@app.post("/api/write_file")
async def write_file(request: WriteFileRequest):
    """Save editor content back to disk. Allowed anywhere inside $HOME."""
    try:
        target = _resolve_user_path(request.filename, WORKSPACE_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(request.content)
        logger.info(f"Saved {target} ({len(request.content)} bytes)")
        return {"ok": True, "filename": str(target), "bytes": len(request.content)}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        logger.error(f"Write Error: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: fastapi.WebSocket):
    """
    PTY-backed terminal. Spawns the user's shell with an OSC 7 hook so every
    prompt emits its working directory, which the frontend uses to sync the
    file explorer (real IDE behavior: cd in terminal -> explorer follows).
    """
    await websocket.accept()
    master_fd, slave_fd = pty.openpty()
    shell = os.environ.get("SHELL", "/bin/bash")
    workspace_root = str(Path(".").resolve())

    # Inject OSC 7 emission into the shell so every prompt reports its cwd.
    # Works for bash, zsh, fish-style POSIX shells via PROMPT_COMMAND / precmd.
    shell_name = os.path.basename(shell)
    env = os.environ.copy()
    env["BROCKSTON_WORKSPACE"] = workspace_root

    # OSC 7 sequence: ESC ] 7 ; file://hostname/path ESC \
    # We install the hook via shell init files so the user never sees the
    # function definition appear at their prompt. This is how VSCode does it.
    import tempfile
    rc_dir = tempfile.mkdtemp(prefix="brockston_rc_")
    shell_args = [shell]

    if "zsh" in shell_name:
        # zsh: ZDOTDIR points to a dir containing .zshrc which sources the
        # user's real .zshrc first, then appends our hook.
        user_zshrc = os.path.expanduser("~/.zshrc")
        zshrc_lines = []
        if os.path.isfile(user_zshrc):
            zshrc_lines.append(f'source "{user_zshrc}"')
        zshrc_lines += [
            '_brockston_cwd_hook() {',
            '  printf "\\033]7;file://%s%s\\033\\\\" "${HOST:-localhost}" "$PWD"',
            '}',
            'typeset -ga precmd_functions',
            'precmd_functions=(${precmd_functions[@]:#_brockston_cwd_hook} _brockston_cwd_hook)',
        ]
        with open(os.path.join(rc_dir, ".zshrc"), "w") as f:
            f.write("\n".join(zshrc_lines) + "\n")
        env["ZDOTDIR"] = rc_dir
        # Don't source global zshenv changes that might override ZDOTDIR
    else:
        # bash: --rcfile points at our wrapper, which sources the user's real
        # bashrc then defines the hook.
        user_bashrc = os.path.expanduser("~/.bashrc")
        rc_path = os.path.join(rc_dir, "bashrc")
        bashrc_lines = []
        if os.path.isfile(user_bashrc):
            bashrc_lines.append(f'source "{user_bashrc}"')
        bashrc_lines += [
            '_brockston_cwd_hook() {',
            '  printf "\\033]7;file://%s%s\\033\\\\" "${HOSTNAME:-localhost}" "$PWD"',
            '}',
            'case ":${PROMPT_COMMAND:-}:" in',
            '  *:_brockston_cwd_hook:*) ;;',
            '  *) PROMPT_COMMAND="_brockston_cwd_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;',
            'esac',
        ]
        with open(rc_path, "w") as f:
            f.write("\n".join(bashrc_lines) + "\n")
        shell_args = [shell, "--rcfile", rc_path, "-i"]

    process = subprocess.Popen(
        shell_args,
        preexec_fn=os.setsid,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        universal_newlines=True,
        env=env,
        cwd=workspace_root,
    )
    os.close(slave_fd)

    # Send the initial working directory to the client immediately.
    await websocket.send_text(json.dumps({
        "type": "cwd",
        "path": workspace_root,
        "workspace": workspace_root,
    }))

    # Track temp dir for cleanup when the process exits.
    process._brockston_rc_dir = rc_dir  # type: ignore[attr-defined]

    async def read_from_pty():
        try:
            while True:
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    output = os.read(master_fd, 10240).decode('utf-8', errors='ignore')
                    if output:
                        await websocket.send_text(json.dumps({"type": "output", "data": output}))
                else:
                    await asyncio.sleep(0.01)
                if process.poll() is not None:
                    break
        except Exception:
            pass

    async def write_to_pty():
        try:
            while True:
                data = await websocket.receive_text()
                if not data or data == '""': continue
                payload = json.loads(data)
                if payload.get("type") == "input":
                    os.write(master_fd, payload.get("data", "").encode())
        except Exception:
            pass

    try:
        await asyncio.gather(read_from_pty(), write_to_pty(), return_exceptions=True)
    finally:
        process.kill()
        # Clean up the temporary rc directory we created for OSC 7 hook injection
        try:
            import shutil
            shutil.rmtree(getattr(process, "_brockston_rc_dir", ""), ignore_errors=True)
        except Exception:
            pass

backend_dir = Path(__file__).parent
frontend_dir = backend_dir / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
