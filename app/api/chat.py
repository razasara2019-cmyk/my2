from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: Request, req: ChatRequest):
    mind = request.app.state.mind
    if not mind:
        return {"response": "⚠️ الوكيل لا يزال يبدأ...", "chat_id": None}
    try:
        response = mind.reflect_on(req.message)
        return {"response": response, "chat_id": None}
    except Exception as e:
        return {"response": f"⚠️ خطأ: {str(e)[:100]}", "chat_id": None}
