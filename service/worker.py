import time
import json
from multiprocessing import Process
from redis_client import redis_client
from translate import translate_batch_grouped
from settings import (
    STREAM_NAME,
    STREAM_GROUP,
    WORKER_POOL,
    BATCH_SIZE,
    BATCH_WAIT_MS,
    MAX_RETRY,
)
CONSUMER_PREFIX = "worker"
# =========================
# 初始化 consumer group
# =========================
def init_stream():
    try:
        redis_client.xgroup_create(
            STREAM_NAME,
            STREAM_GROUP,
            id="0",
            mkstream=True
        )
    except Exception:
        pass
# =========================
# reclaim pending（关键）
# =========================
def reclaim_pending(consumer):
    """
    把超过 60s 没 ack 的任务重新拉回来
    """
    try:
        pending = redis_client.xpending_range(
            STREAM_NAME,
            STREAM_GROUP,
            min="-",
            max="+",
            count=10
        )
        for item in pending:
            msg_id = item["message_id"]
            idle = item["time_since_delivered"]
            # 60秒未处理 → reclaim
            if idle > 60000:
                redis_client.xclaim(
                    STREAM_NAME,
                    STREAM_GROUP,
                    consumer,
                    min_idle_time=60000,
                    message_ids=[msg_id]
                )
    except Exception as e:
        print("[RECLAIM ERROR]", e)
# =========================
# worker loop
# =========================
def worker_loop(worker_id: int):
    consumer = f"{CONSUMER_PREFIX}-{worker_id}"
    buckets = []
    last_flush = time.time()
    print(f"[{consumer}] started", flush=True)
    while True:
        # 1. reclaim pending（防死任务）
        reclaim_pending(consumer)
        # 2. 读取 stream
        resp = redis_client.xreadgroup(
            STREAM_GROUP,
            consumer,
            {STREAM_NAME: ">"},
            count=20,
            block=1000
        )
        if resp:
            for _, messages in resp:
                for msg_id, data in messages:
                    buckets.append({
                        "msg_id": msg_id,
                        "task_id": data["task_id"],
                        "text": data["text"],
                        "src_lang": data.get("src_lang", "en"),
                        "tgt_lang": data.get("tgt_lang", "eng_Latn"),
                        "retry": int(data.get("retry", 0))
                    })
        now = time.time()
        # 3. batch flush 条件
        should_flush = (
            len(buckets) >= BATCH_SIZE or
            (now - last_flush) * 1000 >= BATCH_WAIT_MS
        )
        if should_flush and buckets:
            batch = buckets[:BATCH_SIZE]
            buckets = buckets[BATCH_SIZE:]
            process_batch(batch, consumer)
            last_flush = now
# =========================
# batch 处理（可靠版）
# =========================
def process_batch(batch, consumer):
    try:
        print(f"[{consumer}] start processing batch...", flush=True)
        results = translate_batch_grouped(batch)
        print(f"[{consumer}] batch translation done.", flush=True)
        for item in batch:
            task_id = item["task_id"]
            msg_id = item["msg_id"]
            # ✔ 写结果
            res_text = results.get(task_id, "")
            print(f"[{consumer}] Task {task_id} result: {repr(res_text)}", flush=True)
            redis_client.set(
                f"result:{task_id}",
                res_text,
                ex=3600
            )
            # ✔ ack（成功）
            redis_client.xack(
                STREAM_NAME,
                STREAM_GROUP,
                msg_id
            )
            print(f"[{consumer}] DONE {task_id}", flush=True)
    except Exception as e:
        import traceback
        print(f"[{consumer}] BATCH ERROR:", e, flush=True)
        traceback.print_exc()
        # =========================
        # 失败处理（关键）
        # =========================
        for item in batch:
            task_id = item["task_id"]
            msg_id = item["msg_id"]
            retry = item["retry"]
            if retry >= MAX_RETRY:
                # ❌ 死信队列
                redis_client.set(
                    f"result:{task_id}",
                    f"error: max retry exceeded",
                    ex=3600
                )
                redis_client.xack(
                    STREAM_NAME,
                    STREAM_GROUP,
                    msg_id
                )
            else:
                # 🔁 重新入队
                redis_client.xadd(
                    STREAM_NAME,
                    {
                        "task_id": task_id,
                        "text": item["text"],
                        "src_lang": item["src_lang"],
                        "tgt_lang": item["tgt_lang"],
                        "retry": retry + 1
                    }
                )
                redis_client.xack(
                    STREAM_NAME,
                    STREAM_GROUP,
                    msg_id
                )
# =========================
# main
# =========================
if __name__ == "__main__":
    init_stream()
    p = Process(target=worker_loop, args=(i,))
    p.start()
