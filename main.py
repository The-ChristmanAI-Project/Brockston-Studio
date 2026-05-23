import os
import subprocess
import pty
import select
import json
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel

try:
    from backend.ai_client import get_ai_response
except ImportError:
    from backend.ai_client import get_ai_response
    
try:
    from backend.speech_service import SpeechService
except ImportError:
    from backend.speech_service import SpeechService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrockstonStudio")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
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
        async with httpx.AsyncClient(timeout=5.0) as client:
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
            raise HTTPException(status_code=500, detail=str(inner_e))

# ==========================================
# AUDIO ROUTE (This makes the kids' TTS work)
# ==========================================
@app.post("/api/speech/synthesize")
async def synthesize_speech_route(request: Request):
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files(path: str = ""):
    try:
        if ".." in path or path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid path")
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
             raise HTTPException(status_code=400, detail="Invalid filename")
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "filename": filename}
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    master_fd, slave_fd = pty.openpty()
    shell = os.environ.get("SHELL", "/bin/bash")
    process = subprocess.Popen(
        [shell], preexec_fn=os.setsid, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, universal_newlines=True
    )
    os.close(slave_fd)

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

backend_dir = Path(__file__).parent
frontend_dir = backend_dir.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
