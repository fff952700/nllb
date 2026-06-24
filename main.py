import uvicorn
from fastapi import FastAPI

from conf.loader import load_config
from libs.engine.core import Engine
from libs.models.ct2 import CT2Model
from workers.manager import WorkerManager
from workers.impl_worker import TranslateWorker
from libs.redis.client import RedisClient
from routers.translate import router as translate_router


def main():

    settings = load_config()

    engine = Engine(settings)

    # Redis
    redis = RedisClient(settings.redis)
    engine.bind("redis", redis)
    engine.init_stream()

    # Model
    model = CT2Model(settings.model, settings.runtime)
    engine.bind("model", model)

    # Worker manager
    manager = WorkerManager()
    engine.bind("worker_manager", manager)

    # Workers
    for i in range(settings.worker.pool_size):
        worker = TranslateWorker(engine, i)
        manager.add(worker)

    manager.start()

    # 初始化 FastAPI App
    app = FastAPI()
    app.include_router(translate_router)
    app.state.engine = engine

    print("[system] started")

    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port
    )


if __name__ == "__main__":
    main()
