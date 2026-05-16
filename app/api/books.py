import os
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import MAX_BOOK_SIZE

router = APIRouter(tags=["Books"])


@router.post("/upload-book")
async def upload_book(request: Request, file: UploadFile = File(...)):
    mind = request.app.state.mind
    if not mind or not mind.book_reader:
        raise HTTPException(status_code=503, detail="الوكيل غير جاهز")

    content = await file.read()
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="الملف صغير جداً")
    if len(content) > MAX_BOOK_SIZE:
        raise HTTPException(status_code=400, detail=f"الكتاب كبير جداً (حد أقصى {MAX_BOOK_SIZE // (1024*1024)}MB)")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.txt', '.pdf']:
        raise HTTPException(status_code=400, detail="نوع ملف غير مدعوم. استخدم TXT أو PDF")

    try:
        if ext == '.pdf':
            success, message = mind.book_reader.load_book_from_pdf(file.filename, content)
        else:
            success, message = mind.book_reader.load_book_from_txt(file.filename, content)

        if success:
            return JSONResponse({"status": "success", "message": message})
        raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-book")
async def get_current_book(request: Request):
    mind = request.app.state.mind
    if not mind or not mind.book_reader:
        return {"error": "الوكيل غير جاهز"}
    return {
        "current_book": mind.book_reader.get_current_book(),
        "has_book": mind.book_reader.has_book,
        "text_length": len(mind.book_reader.current_book_text) if mind.book_reader.current_book_text else 0
    }
