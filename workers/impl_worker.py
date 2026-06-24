import time
from multiprocessing import Process


class TranslateWorker(Process):

    def __init__(self, engine, worker_id):
        super().__init__()
        self.engine = engine
        self.worker_id = worker_id

        self.redis = engine.redis
        self.model = engine.model
        self.cfg = engine.settings

        self.stream = self.cfg.stream.name
        self.group = self.cfg.stream.group

        self.batch_size = self.cfg.worker.batch_size
        self.batch_wait = self.cfg.worker.batch_wait_ms

    def run(self):

        consumer = f"worker-{self.worker_id}"
        buckets = []
        last_flush = time.time()

        print(f"[{consumer}] started", flush=True)

        # 提前在子进程中加载模型，避免第一个请求卡顿
        try:
            if hasattr(self.model, "load"):
                self.model.load()
        except Exception as e:
            print(f"[{consumer}] model load error: {e}")

        try:
            while True:

                if buckets:
                    elapsed_ms = (time.time() - last_flush) * 1000
                    remaining_ms = self.batch_wait - elapsed_ms
                    block_time = max(1, int(remaining_ms))
                else:
                    block_time = 1000

                resp = self.redis.xreadgroup(
                    self.group,
                    consumer,
                    {self.stream: ">"},
                    count=20,
                    block=block_time
                )

                if resp:
                    for _, messages in resp:
                        for msg_id, data in messages:

                            buckets.append({
                                "msg_id": msg_id,
                                "task_id": data["task_id"],
                                "text": data["text"],
                                "src_lang": data.get("src_lang"),
                                "tgt_lang": data.get("tgt_lang"),
                            })

                now = time.time()

                if len(buckets) >= self.batch_size or (now - last_flush) * 1000 >= self.batch_wait:

                    if buckets:
                        batch = buckets[:self.batch_size]
                        buckets = buckets[self.batch_size:]

                        self.process(batch)
                        last_flush = now
        except KeyboardInterrupt:
            print(f"[{consumer}] shutting down gracefully...")
        except Exception as e:
            print(f"[{consumer}] unexpected error: {e}")

    def process(self, batch):

        try:
            import time
            t0 = time.time()
            results = self.model.translate_batch(batch)
            t1 = time.time()
            # print(f"[{self.name}] translated batch of {len(batch)} in {t1 - t0:.3f}s", flush=True)

            for item in batch:

                task_id = item["task_id"]
                msg_id = item["msg_id"]

                text = results.get(task_id, "")

                self.redis.set(f"result:{task_id}", text, ex=3600)
                self.redis.publish(f"notify:{task_id}", text)

                self.redis.xack(
                    self.stream,
                    self.group,
                    msg_id
                )

        except Exception as e:
            print("[BATCH ERROR]", e)
