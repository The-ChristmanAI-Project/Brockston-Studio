# claude_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
import os

router = APIRouter()

class ClaudeRequest(BaseModel):
    messages: list
    system: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

@router.post("/api/claude")
async def call_claude(req: ClaudeRequest):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY environment variable not set")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=req.model,
            max_tokens=req.max_tokens,
            system=req.system,
            messages=req.messages
        )
        return {"content": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))