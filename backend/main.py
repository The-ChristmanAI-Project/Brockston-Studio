import os
import logging
import subprocess
import pty
import select
import json
import asyncio
import tempfile
from typing import List, Optional
from pathlib import Path
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Request # pyright: ignore[reportMissingImports]
from fastapi.responses import Response # pyright: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]

from config import OLLAMA_BASE_URL, LLM_MODEL_CODER, BROCKSTON_WORKSPACE
from brockston_client import BrockstonClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brockston-studio")

app = FastAPI(title="Brockston IDE Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

agent = BrockstonClient(base_url=OLLAMA_BASE_URL, model=LLM_MODEL_CODER)

class ChatRequest(BaseModel):
    messages: List
    context: Optional[dict] = None

class SuggestFixRequest(BaseModel):
    code: str
    instruction: str
    path: Optional[str] = None

class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: float = 5.0

class SpeakRequest(BaseModel):
    text: str
    voice: str = "default"

@app.get("/")
async def root():
    return {"status": "online", "model": LLM_MODEL_CODER}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        reply = await agent.chat(messages=request.messages, context=request.context)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suggest_fix")
async def suggest_fix(request: SuggestFixRequest):
    try:
        return await agent.suggest_fix(
            code=request.code, 
            instruction=request.instruction, 
            path=request.path
        )
    except Exception as e:
        logger.error(f"Suggest fix error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files(path: str = ""):
    try:
        target_dir = os.path.join(BROCKSTON_WORKSPACE, path) if path else BROCKSTON_WORKSPACE
        if not os.path.isdir(target_dir):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        files = []
        for item in os.listdir(target_dir):
            if not item.startswith('.'):
                item_path = os.path.join(target_dir, item)
                kind = "folder" if os.path.isdir(item_path) else "file"
                files.append({"name": item, "type": kind})
        
        return {"files": sorted(files, key=lambda x: (x != "folder", x ))}
    except Exception as e:
        logger.error(f"File listing error: {e}")
        return {"files": []}

@app.post("/api/execute")
async def execute_code(request: ExecuteRequest):
    """Execute code safely with timeout"""
    try:
        import subprocess
        import time
        
        code = request.code
        language = request.language
        timeout = min(request.timeout, 10.0)  # Max 10 seconds
        
        if language not in ["python"]:
            raise HTTPException(status_code=400, detail="Language not supported")
        
        # Write code to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        finally:
            import os
            os.unlink(temp_file)
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Code execution timed out after {timeout} seconds"
        }
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio to text (currently mock)"""
    try:
        audio_data = await file.read()
        
        # For now, return mock transcription
        # In future: integrate with speech_service.transcribe_audio()
        return {
            "text": "[Speech input - students can speak into browser microphone]",
            "confidence": 0.75,
            "filename": file.filename,
            "size": len(audio_data)
        }
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/speak")
async def synthesize_speech(request: SpeakRequest):
    """Synthesize text to speech"""
    try:
        from speech_service import synthesize_speech
        
        text = request.text
        voice = request.voice
        
        # Generate audio bytes
        audio_bytes = await synthesize_speech(text, voice)
        
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/git/clone")
async def git_clone_repo(url: str, name: Optional[str] = None):
    """Clone a GitHub repository"""
    try:
        from git_service import clone_repo
        from pathlib import Path
        
        repo_path = clone_repo(url, name)
        return {
            "success": True,
            "path": str(repo_path),
            "url": url
        }
    except Exception as e:
        logger.error(f"Git clone error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/git/commit")
async def git_commit(path: str, message: str = "Student work"):
    """Commit changes to git"""
    try:
        import subprocess
        
        result = subprocess.run(
            ["git", "-C", path, "add", "."],
            capture_output=True,
            text=True
        )
        
        result = subprocess.run(
            ["git", "-C", path, "commit", "-m", message],
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "message": message,
            "output": result.stdout
        }
    except Exception as e:
        logger.error(f"Git commit error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/git/status")
async def git_status(path: str):
    """Get git repository status"""
    try:
        import subprocess
        
        result = subprocess.run(
            ["git", "-C", path, "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        
        return {
            "has_changes": bool(result.stdout.strip()),
            "status": result.stdout,
            "path": path
        }
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return {"error": str(e)}

@app.get("/api/read_file")
async def read_file(filename: str):
    try:
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        filepath = os.path.join(BROCKSTON_WORKSPACE, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"content": content, "filename": filename}
    except Exception as e:
        logger.error(f"Read error: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    
    try:
        master_fd, slave_fd = pty.openpty()
        shell = os.environ.get("SHELL", "/bin/bash")
        
        process = subprocess.Popen(
            [shell],
            preexec_fn=os.setsid,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            universal_newlines=True
        )
        
        os.close(slave_fd)
        
        async def read_from_pty():
            while True:
                try:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                    if master_fd in r:
                        output = os.read(master_fd, 10240).decode('utf-8', errors='ignore')
                        if output:
                            await websocket.send_text(json.dumps({"type": "output", "data": output}))
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"PTY read error: {e}")
                    break
        
        async def write_to_pty():
            while True:
                try:
                    data = await websocket.receive_text()
                    payload = json.loads(data)
                    if payload.get("type") == "input":
                        cmd = payload.get("data", "")
                        os.write(master_fd, (cmd + "\n").encode())
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"PTY write error: {e}")
                    break
        
        await asyncio.gather(read_from_pty(), write_to_pty())
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            os.close(master_fd)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
