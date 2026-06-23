import uuid
import time
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from redis_client import redis_client
from rate_limit import rate_limit
from settings import STREAM_NAME, AUTH_ENABLED

app = FastAPI(title="NLLB Sync API")


class Req(BaseModel):
    text: str
    src_lang: str | None = None   # ⭐ 支持自定义源语言
    tgt_lang: str = "zho_Hans"    # ⭐ 目标语言


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/translate")
def translate_api(req: Req, request: Request):

    api_key = getattr(request.state, "api_key", "anonymous")

    if not rate_limit(api_key):
        raise HTTPException(429, "rate limit exceeded")

    task_id = str(uuid.uuid4())

    # ✔ 投递任务（完整语言信息）
    redis_client.xadd(
        STREAM_NAME,
        {
            "task_id": task_id,
            "text": req.text,
            "src_lang": req.src_lang or "",
            "tgt_lang": req.tgt_lang
        }
    )

    # ✔ 同步等待（短阻塞）
    timeout = 30
    start = time.time()

    while True:

        result = redis_client.get(f"result:{task_id}")

        if result is not None:
            return {
                "task_id": task_id,
                "src_lang": req.src_lang,
                "tgt_lang": req.tgt_lang,
                "result": result,
                "mode": "sync"
            }

        if time.time() - start > timeout:
            raise HTTPException(
                status_code=504,
                detail={
                    "task_id": task_id,
                    "error": "timeout"
                }
            )

        time.sleep(0.05)
