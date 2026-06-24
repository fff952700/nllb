class BaseWorker:

    def __init__(self, engine, worker_id):
        """
        ✔ 统一依赖入口：engine
        """

        self.engine = engine
        self.worker_id = worker_id

        # ===== 统一依赖 =====
        self.redis = engine.redis
        self.config = engine.config
        self.translator = engine.model

        self.running = True

    def run(self):
        raise NotImplementedError

    def stop(self):
        self.running = False
