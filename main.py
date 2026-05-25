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

@app.get("/api/files")
async def list_files(path: str = ""):
    try:
        if ".." in path or path.startswith("/"):
            raise fastapi.HTTPException(status_code=400, detail="Invalid path")
        root_dir = path if path else "."
        files = []
        for item in os.listdir(root_dir):
            if not item.startswith(".") and not item.startswith("__"):
                full_path = os.path.join(root_dir, item)
                if os.path.isfile(full_path) or os.path.isdir(full_path):
                    kind = "folder" if os.path.isdir(full_path) else "file"
                    files.append({"name": item, "type": kind})
        return {"files": files, "path": path}
    except Exception as e:
        logger.error(f"File Listing Error: {e}")
        return {"files": [], "path": path}

@app.get("/api/read_file")
async def read_file(filename: str):
    try:
        if ".." in filename or filename.startswith("/"):
             raise fastapi.HTTPException(status_code=400, detail="Invalid filename")
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "filename": filename}
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise fastapi.HTTPException(status_code=404, detail="File not found")

class WriteFileRequest(BaseModel):
    filename: str
    content: str

@app.post("/api/write_file")
async def write_file(request: WriteFileRequest):
    """Save editor content back to disk. Sandboxed to workspace root."""
    try:
        filename = request.filename
        if ".." in filename or filename.startswith("/"):
            raise fastapi.HTTPException(status_code=400, detail="Invalid filename")
        target = Path(filename).resolve()
        workspace = Path(".").resolve()
        # Make sure the target stays inside the workspace
        try:
            target.relative_to(workspace)
        except ValueError:
            raise fastapi.HTTPException(status_code=400, detail="Path outside workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(request.content)
        logger.info(f"Saved {filename} ({len(request.content)} bytes)")
        return {"ok": True, "filename": filename, "bytes": len(request.content)}
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
