from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class FeedbackRequest(BaseModel):
    chat_id: int
    feedback: bool


@router.post("/chat")
async def chat(request: Request, req: ChatRequest):
    mind = request.app.state.mind
    if not mind:
        return {"response": "⚠️ الكيان لا يزال يبدأ...", "chat_id": None}
    try:
        response = mind.reflect_on(req.message)
        return {"response": response, "chat_id": None}
    except Exception as e:
        return {"response": f"⚠️ خطأ: {str(e)[:100]}", "chat_id": None}


@router.post("/feedback")
async def submit_feedback(request: Request, req: FeedbackRequest):
    # تسجيل التقييم (يمكن تخزينه في قاعدة البيانات لاحقاً)
    return {"status": "success"}


@router.get("/pending-questions")
async def get_pending_questions(request: Request):
    mind = request.app.state.mind
    if not mind:
        return {"questions": []}
    return {"questions": mind.questions.get_all_unanswered()}
