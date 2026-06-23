from dataclasses import dataclass


@dataclass
class ServerConfig:
    host: str
    port: int


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str
    max_connections: int


@dataclass
class StreamConfig:
    name: str
    group: str


@dataclass
class WorkerConfig:
    pool_size: int
    batch_size: int
    batch_wait_ms: int
    max_retry: int


@dataclass
class ModelConfig:
    name: str
    ct2_path: str
    max_length: int


@dataclass
class GPUConfig:
    max_tokens: int
    min_batch: int
    max_batch: int
    stash_max_age_ms: int


@dataclass
class HFConfig:
    token: str
    cache_dir: str


@dataclass
class RuntimeConfig:
    omp_threads: int
    mkl_threads: int


@dataclass
class RateLimitConfig:
    enabled: bool
    limit: int
    window: int


@dataclass
class Settings:
    mode: str               # "cpu" | "gpu"
    server: ServerConfig
    redis: RedisConfig
    stream: StreamConfig
    worker: WorkerConfig
    model: ModelConfig
    gpu: GPUConfig
    hf: HFConfig
    runtime: RuntimeConfig
    rate_limit: RateLimitConfig
