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
from config import OLLAMA_BASE_URL, LLM_MODEL_CODER, BROCKSTON_WORKSPACE, SERVER_HOST, SERVER_PORT
from brockston_client import BrockstonClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brockston-studio")
app = FastAPI()

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

@app.get("/")
async def root():
    return {"status": "online", "workspace": BROCKSTON_WORKSPACE}

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
        logger.error(f"Read error: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/chat")
async def chat_endpoint(request: SimpleChatRequest):
    try:
        logger.info(f"Chat request: {request.message}")
        reply = await agent.chat(messages=[{"role": "user", "content": request.message}])
        return {"response": reply}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brockston/chat")
async def chat_with_brockston(request: ChatRequest):
    reply = await agent.chat(messages=request.messages, context=request.context)
    return {"reply": reply}

@app.post("/api/brockston/suggest_fix")
async def suggest_fix(request: SuggestFixRequest):
    return await agent.suggest_fix(code=request.code, instruction=request.instruction, path=request.path)

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
