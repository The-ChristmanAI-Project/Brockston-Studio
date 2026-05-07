import os
import logging
import subprocess
import pty
import select
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import OLLAMA_BASE_URL, LLM_MODEL_GENERAL, LLM_MODEL_CODER, LLM_PROVIDER, BROCKSTON_BASE_URL, ULTIMATEEV_BASE_URL, resolve_path, WORKSPACE_ROOT
from .brockston_client import BrockstonClient
from .claude_router import router as claude_router
from .git_service import clone_repo
from .speech_service import SpeechService

# Setup Logging
from config import OLLAMA_BASE_URL, LLM_MODEL_CODER, BROCKSTON_WORKSPACE, SERVER_HOST, SERVER_PORT
from brockston_client import BrockstonClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brockston-studio")
app = FastAPI()

# --- CORS POLICY (The Fix for "Failed to Fetch") ---
origins = [
    "http://localhost:7777",
    "http://127.0.0.1:7777",
    "*"  # Open for dev speed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = BrockstonClient(base_url=OLLAMA_BASE_URL, model=LLM_MODEL_CODER)

class SimpleChatRequest(BaseModel):
    message: str

class SuggestFixRequest(BaseModel):
    code: str
    instruction: str
    path: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[dict]
    context: Optional[dict] = None
    model: Optional[str] = None

class BrockstonSuggestFixRequest(BaseModel):
    instruction: str
    path: str
    code: str
    model: Optional[str] = None

# --- API ENDPOINTS ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "10 Toes Down",
        "system": "Online",
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
        
        return {"files": sorted(files, key=lambda x: (x["type"] != "folder", x["name"]))}
    except Exception as e:
        logger.error(f"File listing error: {e}")
        return {"files": []}

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
        logger.error(f"Read Error: {e}")
        raise HTTPException(status_code=404, detail="File not found or unreadable")

# --- TERMINAL WEBSOCKET (FIXED VERSION) ---
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
                    else:
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
                        os.write(master_fd, cmd.encode())
                except WebSocketDisconnect:
                    process.terminate()
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
