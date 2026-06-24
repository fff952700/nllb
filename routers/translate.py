from fastapi import APIRouter, Request
from service.translate_service import process_translation

router = APIRouter()

@router.post("/translate")
def translate(req: dict, request: Request):

    engine = request.app.state.engine
    
    text = req.get("text", "")
    src_lang = req.get("src_lang", "")
    tgt_lang = req.get("tgt_lang", "")

    return process_translation(engine, text, src_lang, tgt_lang)
