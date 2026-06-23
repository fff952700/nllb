import time
import traceback
from multiprocessing import Process
from typing import List, Dict, Any

from conf.setting import StreamConfig, WorkerConfig
from lib.redis.client import RedisClient
from service.base import BaseWorker, BaseTranslator

CONSUMER_PREFIX = "cpu-worker"


def _worker_loop(
    worker_id: int,
    translator: BaseTranslator,
    redis_cfg,
    stream_cfg: StreamConfig,
    worker_cfg: WorkerConfig,
):
    """在子进程中运行的 worker 主循环（顶层函数，方便 pickle 序列化）"""

    # 子进程内重建 RedisClient（避免跨进程共享连接池问题）
    from lib.redis.client import RedisClient
    redis_client = RedisClient(redis_cfg)

    consumer = f"{CONSUMER_PREFIX}-{worker_id}"
    buckets: List[Dict[str, Any]] = []
    last_flush = time.time()

    print(f"[{consumer}] started", flush=True)

    while True:
        # 1. reclaim 超时未 ack 的消息
        _reclaim_pending(redis_client, consumer, stream_cfg)

        # 2. 从 stream 读取新消息
        resp = redis_client.xreadgroup(
            stream_cfg.group,
            consumer,
            {stream_cfg.name: ">"},
            count=20,
            block=1000,
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
                        "retry": int(data.get("retry", 0)),
                    })

        now = time.time()

        # 3. batch flush 条件
        should_flush = (
            len(buckets) >= worker_cfg.batch_size
            or (now - last_flush) * 1000 >= worker_cfg.batch_wait_ms
        )

        if should_flush and buckets:
            batch = buckets[:worker_cfg.batch_size]
            buckets = buckets[worker_cfg.batch_size:]
            _process_batch(batch, consumer, translator, redis_client, stream_cfg, worker_cfg)
            last_flush = now


def _reclaim_pending(redis_client: RedisClient, consumer: str, stream_cfg: StreamConfig):
    """把超过 60s 没有 ack 的消息重新归属到当前 consumer"""
    try:
        pending = redis_client.xpending_range(
            stream_cfg.name, stream_cfg.group, min="-", max="+", count=10
        )
        for item in pending:
            if item["time_since_delivered"] > 60000:
                redis_client.xclaim(
                    stream_cfg.name, stream_cfg.group, consumer,
                    min_idle_time=60000,
                    message_ids=[item["message_id"]],
                )
    except Exception as e:
        print(f"[RECLAIM ERROR] {e}", flush=True)


def _process_batch(
    batch: List[Dict],
    consumer: str,
    translator: BaseTranslator,
    redis_client: RedisClient,
    stream_cfg: StreamConfig,
    worker_cfg: WorkerConfig,
):
    try:
        print(f"[{consumer}] processing batch of {len(batch)}...", flush=True)
        results = translator.translate_batch(batch)
        print(f"[{consumer}] batch done.", flush=True)

        for item in batch:
            task_id = item["task_id"]
            msg_id = item["msg_id"]
            res_text = results.get(task_id, "")
            redis_client.set(f"result:{task_id}", res_text, ex=3600)
            redis_client.xack(stream_cfg.name, stream_cfg.group, msg_id)
            print(f"[{consumer}] DONE {task_id}", flush=True)

    except Exception as e:
        print(f"[{consumer}] BATCH ERROR: {e}", flush=True)
        traceback.print_exc()

        for item in batch:
            task_id = item["task_id"]
            msg_id = item["msg_id"]
            retry = item["retry"]

            if retry >= worker_cfg.max_retry:
                redis_client.set(f"result:{task_id}", "error: max retry exceeded", ex=3600)
                redis_client.xack(stream_cfg.name, stream_cfg.group, msg_id)
            else:
                redis_client.xadd(
                    stream_cfg.name,
                    {
                        "task_id": task_id,
                        "text": item["text"],
                        "src_lang": item["src_lang"],
                        "tgt_lang": item["tgt_lang"],
                        "retry": retry + 1,
                    },
                )
                redis_client.xack(stream_cfg.name, stream_cfg.group, msg_id)


class CPUWorker(BaseWorker):
    """CPU Worker：启动多进程从 Redis 流读取任务，调用 CPUTranslator 处理"""

    def __init__(
        self,
        translator: BaseTranslator,
        redis_client: RedisClient,
        stream_cfg: StreamConfig,
        worker_cfg: WorkerConfig,
    ):
        super().__init__(translator, redis_client, stream_cfg, worker_cfg)
        self._processes: List[Process] = []

    def _init_stream(self):
        """确保 Redis stream consumer group 存在"""
        try:
            self.redis.xgroup_create(
                self.stream_cfg.name,
                self.stream_cfg.group,
                id="0",
                mkstream=True,
            )
        except Exception:
            pass  # group 已存在时会抛异常，忽略即可

    def start(self) -> None:
        self._init_stream()
        for i in range(self.worker_cfg.pool_size):
            p = Process(
                target=_worker_loop,
                args=(
                    i,
                    self.translator,
                    self.redis._client.connection_pool.connection_kwargs,  # 传递连接参数而非连接池
                    self.stream_cfg,
                    self.worker_cfg,
                ),
                daemon=True,
            )
            p.start()
            self._processes.append(p)
            print(f"[CPUWorker] started process {i} (pid={p.pid})", flush=True)

    def stop(self) -> None:
        for p in self._processes:
            p.terminate()
        self._processes.clear()
        print("[CPUWorker] all processes stopped.", flush=True)
