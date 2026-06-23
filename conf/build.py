import os
from .loader import load_yaml
from .setting import (
    Settings, ServerConfig, RedisConfig, StreamConfig,
    WorkerConfig, ModelConfig, GPUConfig, HFConfig,
    RuntimeConfig, RateLimitConfig,
)


def build_settings(path: str) -> Settings:
    raw = load_yaml(path)

    hf_cfg = HFConfig(**raw["hf"])
    rt_cfg = RuntimeConfig(**raw["runtime"])

    settings = Settings(
        mode=raw.get("mode", "cpu"),
        server=ServerConfig(**raw["server"]),
        redis=RedisConfig(**raw["redis"]),
        stream=StreamConfig(**raw["stream"]),
        worker=WorkerConfig(**raw["worker"]),
        model=ModelConfig(**raw["model"]),
        gpu=GPUConfig(**raw["gpu"]),
        hf=hf_cfg,
        runtime=rt_cfg,
        rate_limit=RateLimitConfig(**raw["rate_limit"]),
    )

    # 应用运行时环境变量
    os.environ["HF_HOME"] = settings.hf.cache_dir
    if settings.hf.token:
        os.environ["HF_TOKEN"] = settings.hf.token
    os.environ["OMP_NUM_THREADS"] = str(settings.runtime.omp_threads)
    os.environ["MKL_NUM_THREADS"] = str(settings.runtime.mkl_threads)

    return settings
