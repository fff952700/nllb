import os
import yaml
from .settings import *


def load_config(path: str = None) -> Settings:
    """
    ✔ 唯一 config 入口
    """
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__),
            "config.yaml"
        )

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    s = Settings(
        mode=raw.get("mode", "cpu"),

        server=ServerConfig(**raw["server"]),
        redis=RedisConfig(**raw["redis"]),
        stream=StreamConfig(**raw["stream"]),
        worker=WorkerConfig(**raw["worker"]),
        model=ModelConfig(**raw["model"]),
        gpu=GPUConfig(**raw["gpu"]),
        hf=HFConfig(**raw["hf"]),
        runtime=RuntimeConfig(**raw.get("runtime", {})),
        rate_limit=RateLimitConfig(**raw["rate_limit"]),
    )

    # env
    os.environ["HF_HOME"] = s.hf.cache_dir
    if s.hf.token:
        os.environ["HF_TOKEN"] = s.hf.token

    os.environ["OMP_NUM_THREADS"] = str(s.runtime.omp_threads)
    os.environ["MKL_NUM_THREADS"] = str(s.runtime.mkl_threads)

    return s
