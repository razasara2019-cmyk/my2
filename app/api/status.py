from fastapi import APIRouter, Request

router = APIRouter(tags=["Status"])


@router.get("/status")
async def get_status(request: Request):
    mind = request.app.state.mind
    if not mind:
        return {"ready": False, "version": "2.0.0"}
    return mind.get_status()


@router.get("/mood")
async def get_mood(request: Request):
    mind = request.app.state.mind
    if not mind:
        return {"mood": "هادئ"}
    return {"mood": mind.mood, "consciousness": mind.consciousness}
