import os
import subprocess
import pty
import select
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from .config import OLLAMA_BASE_URL, LLM_MODEL_GENERAL, LLM_MODEL_CODER, LLM_PROVIDER, BROCKSTON_BASE_URL, ULTIMATEEV_BASE_URL, resolve_path, WORKSPACE_ROOT
from .brockston_client import BrockstonClient
from .claude_router import router as claude_router
from .git_service import clone_repo
from .speech_service import SpeechService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrockstonStudio")

# Initialize AI clients
brockston_client = BrockstonClient(base_url=BROCKSTON_BASE_URL, provider="brockston", model="brockston")
ultimateev_client = BrockstonClient(base_url=ULTIMATEEV_BASE_URL, provider="ultimateev", model="ultimateev")
ollama_client = BrockstonClient(base_url=OLLAMA_BASE_URL, provider=LLM_PROVIDER, model=LLM_MODEL_GENERAL)

def get_client_for_model(model_name: str):
    """Get the appropriate client based on model name."""
    model_lower = model_name.lower() if model_name else "brockston"

    if model_lower == "brockston":
        return brockston_client
    elif model_lower == "ultimateev":
        return ultimateev_client
    else:
        # Default to Ollama for other models
        return ollama_client

app = FastAPI()

# --- CORS POLICY (The Fix for "Failed to Fetch") ---
origins = [
    "http://localhost:5055",
    "http://127.0.0.1:5055",
    "*"  # Open for dev speed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Claude router
app.include_router(claude_router)

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    message: str

class BrockstonChatRequest(BaseModel):
    messages: list[dict]
    context: Optional[dict] = None
    model: Optional[str] = None

class BrockstonSuggestFixRequest(BaseModel):
    instruction: str
    path: str
    code: str
    model: Optional[str] = None

# --- API ENDPOINTS ---

# Initialize speech service
speech_service = SpeechService()

@app.get("/api/health")
async def health_check():
    return {
        "status": "10 Toes Down",
        "system": "Online",
        "workspace": str(WORKSPACE_ROOT),
        "llm_provider": LLM_PROVIDER,
        "llm_model_general": LLM_MODEL_GENERAL,
        "llm_model_coder": LLM_MODEL_CODER,
        "ollama_url": OLLAMA_BASE_URL,
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Sending to LLM provider {LLM_PROVIDER} model {LLM_MODEL_GENERAL}: {request.message}")
        client = get_client_for_model(LLM_MODEL_GENERAL)
        reply = await client.chat(
            [
                {
                    "role": "system",
                    "content": "You are BROCKSTON, the code reasoning engine for Everett, the architect. Answer Everett directly, with precision and clarity.",
                },
                {"role": "user", "content": request.message},
            ],
            None,
            model=LLM_MODEL_GENERAL,
        )
        return {"response": reply}
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brockston/chat")
async def brockston_chat(request: BrockstonChatRequest):
    try:
        response_model = request.model or LLM_MODEL_GENERAL
        client = get_client_for_model(response_model)
        logger.info(f"BROCKSTON chat using model {response_model} with client {client.provider}")
        reply = await client.chat(
            request.messages,
            request.context,
            model=response_model,
        )
        return {"reply": reply}
    except Exception as e:
        logger.error(f"BROCKSTON chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brockston/suggest_fix")
async def brockston_suggest_fix(request: BrockstonSuggestFixRequest):
    try:
        response_model = request.model or LLM_MODEL_CODER
        client = get_client_for_model(response_model)
        logger.info(f"BROCKSTON suggest_fix using model {response_model} with client {client.provider}")
        result = await client.suggest_fix(
            code=request.code,
            instruction=request.instruction,
            path=request.path,
            model=response_model,
        )
        return {
            "proposed_code": result.get("proposed_code", ""),
            "summary": result.get("summary", ""),
        }
    except Exception as e:
        logger.error(f"BROCKSTON suggest_fix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files(path: str = ""):
    """Lists files in the specified directory (excluding hidden/system)"""
    try:
        # Security: prevent directory traversal
        if ".." in path or path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Determine directory to list
        if path:
            root_dir = path
        else:
            root_dir = "."
        
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
    """Reads content of a file for the editor"""
    try:
        # Security: Basic prevention of directory traversal
        if ".." in filename or filename.startswith("/"):
             raise HTTPException(status_code=400, detail="Invalid filename")

        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "filename": filename}
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise HTTPException(status_code=404, detail="File not found or unreadable")


# --- SECURE FILE OPERATIONS (using resolve_path) ---

class FileOpenRequest(BaseModel):
    path: str

class FileSaveRequest(BaseModel):
    path: str
    content: str

@app.get("/api/files/open")
async def open_file(path: str):
    """Securely opens a file within the workspace"""
    try:
        resolved_path = resolve_path(path)
        if not resolved_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"path": str(resolved_path), "content": content}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"File open error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/save")
async def save_file(request: FileSaveRequest):
    """Securely saves a file within the workspace"""
    try:
        resolved_path = resolve_path(request.path)
        
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        
        logger.info(f"File saved: {resolved_path}")
        return {"status": "ok", "path": str(resolved_path)}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"File save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/list")
async def list_workspace_files(path: str = ""):
    """Lists files in a workspace directory securely"""
    try:
        if path:
            dir_path = resolve_path(path)
        else:
            dir_path = WORKSPACE_ROOT
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        files = []
        for item in dir_path.iterdir():
            if item.name.startswith(".") or item.name.startswith("__"):
                continue
            kind = "folder" if item.is_dir() else "file"
            files.append({"name": item.name, "type": kind})
        
        return {"files": files, "path": str(dir_path)}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"File listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- GIT OPERATIONS ---

class GitCloneRequest(BaseModel):
    git_url: str
    folder_name: Optional[str] = None

@app.post("/api/git/clone")
async def git_clone(request: GitCloneRequest):
    """Clone a Git repository into the workspace"""
    try:
        cloned_path = clone_repo(request.git_url, request.folder_name)
        return {
            "status": "ok",
            "local_path": str(cloned_path),
            "workspace_name": cloned_path.name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Git clone error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- SPEECH OPERATIONS ---

from fastapi import UploadFile, File as FileDep

@app.post("/api/speech/transcribe")
async def transcribe_audio(audio: UploadFile = FileDep(...)):
    """Transcribe audio to text"""
    try:
        audio_data = await audio.read()
        transcribed_text = await speech_service.transcribe_audio(audio_data, audio.filename)
        return {"text": transcribed_text}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/speech/synthesize")
async def synthesize_speech(text: str, voice: str = "alloy"):
    """Synthesize speech from text"""
    try:
        audio_data = await speech_service.synthesize_speech(text, voice)
        return Response(content=audio_data, media_type="audio/mpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SpeechChatRequest(BaseModel):
    messages: list[dict]
    context: Optional[dict] = None
    model: Optional[str] = None
    voice: Optional[str] = "alloy"

@app.post("/api/speech/chat")
async def speech_chat(request: SpeechChatRequest):
    """Process speech chat and return audio response"""
    try:
        # Get AI response
        client = get_client_for_model(request.model or LLM_MODEL_GENERAL)
        reply = await client.chat(request.messages, request.context, model=request.model)
        
        # Synthesize speech
        audio_data = await speech_service.synthesize_speech(reply, request.voice or "alloy")
        
        from fastapi.responses import Response
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"X-Response-Text": reply}
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Speech chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- TERMINAL WEBSOCKET (FIXED VERSION) ---
@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    logger.info("Terminal WebSocket connection accepted")

    # Create a pseudo-terminal
    master_fd, slave_fd = pty.openpty()

    # Start a shell (zsh if available, else bash)
    shell = os.environ.get("SHELL", "/bin/bash")

    # Run the process attached to the PTY
    process = subprocess.Popen(
        [shell],
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True
    )

    os.close(slave_fd)  # Close slave in parent
    logger.info(f"Shell process started with PID: {process.pid}")

    # Task for reading from PTY and sending to websocket
    async def read_from_pty():
        """Read output from the shell and send to websocket"""
        try:
            while True:
                # Non-blocking check for data
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    try:
                        output = os.read(master_fd, 10240).decode('utf-8', errors='ignore')
                        if output:
                            await websocket.send_text(json.dumps({"type": "output", "data": output}))
                    except OSError as e:
                        logger.error(f"PTY read error: {e}")
                        break
                else:
                    # Yield control to event loop
                    await asyncio.sleep(0.01)
                    
                # Check if process is still alive
                if process.poll() is not None:
                    logger.info("Shell process terminated")
                    break
        except Exception as e:
            logger.error(f"Error in read_from_pty: {e}")
        finally:
            logger.info("read_from_pty task finished")

    # Task for receiving from websocket and writing to PTY
    async def write_to_pty():
        """Receive input from websocket and write to shell"""
        try:
            while True:
                data = await websocket.receive_text()
                
                # Handle empty keepalive messages
                if not data or data == '""':
                    continue
                    
                try:
                    payload = json.loads(data)
                    if payload.get("type") == "input":
                        cmd = payload.get("data", "")
                        os.write(master_fd, cmd.encode())
                    elif payload.get("type") == "resize":
                        # Handle terminal resize if needed in the future
                        pass
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")
                except OSError as e:
                    logger.error(f"PTY write error: {e}")
                    break
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error in write_to_pty: {e}")
        finally:
            logger.info("write_to_pty task finished")

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            read_from_pty(),
            write_to_pty(),
            return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Terminal session error: {e}")
    finally:
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=1)
        except:
            process.kill()
        try:
            os.close(master_fd)
        except:
            pass
        logger.info("Terminal session cleaned up")

# --- STATIC FILES SERVING (FIXED WITH ABSOLUTE PATH) ---
# Get the absolute path to the frontend directory
backend_dir = Path(__file__).parent
frontend_dir = backend_dir.parent / "frontend"

logger.info(f"Serving static files from: {frontend_dir}")

app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
