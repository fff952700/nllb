import os
import yaml

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)


# =========================
# server
# =========================
HOST = cfg["server"]["host"]
PORT = cfg["server"]["port"]

# =========================
# auth
# =========================
AUTH_ENABLED = cfg["auth"]["enabled"]

# =========================
# worker
# =========================
WORKER_POOL = cfg["worker"]["pool_size"]
BATCH_SIZE = cfg["worker"]["batch_size"]
BATCH_WAIT_MS = cfg["worker"]["batch_wait_ms"]
MAX_RETRY = cfg["worker"]["max_retry"]

# =========================
# stream
# =========================
STREAM_NAME = cfg["stream"]["name"]
STREAM_GROUP = cfg["stream"]["group"]

# =========================
# redis
# =========================
REDIS_HOST = cfg["redis"]["host"]
REDIS_PORT = cfg["redis"]["port"]
REDIS_DB = cfg["redis"]["db"]
REDIS_PASSWORD = cfg["redis"]["password"]
REDIS_MAX_CONN = cfg["redis"]["max_connections"]


# =========================
# model
# =========================
MODEL_NAME = cfg["model"]["name"]
CT2_PATH = cfg["model"].get("ct2_path")
MAX_LENGTH = cfg["model"]["max_length"]

# =========================
# translate
# =========================
DEFAULT_TARGET_LANG = cfg["translate"]["default_target_lang"]

# =========================
# cache
# =========================
CACHE_EXPIRE = cfg["cache"]["expire"]

# =========================
# HF fix（关键）
# =========================
hf = cfg["hf"]
HF_CACHE_DIR = hf["cache_dir"]

os.environ["HF_HOME"] = HF_CACHE_DIR

if hf.get("token"):
    os.environ["HF_TOKEN"] = hf["token"]

# =========================
# runtime
# =========================
rt = cfg["runtime"]
os.environ["OMP_NUM_THREADS"] = str(rt["omp_threads"])
os.environ["MKL_NUM_THREADS"] = str(rt["mkl_threads"])

# rate
RL_ENABLED = cfg["rate_limit"]["enabled"]
RL_LIMIT = cfg["rate_limit"]["limit"]
RL_WINDOW = cfg["rate_limit"]["window"]

# =========================
# gpu scheduler（新增）
# =========================
GPU_MAX_TOKENS = cfg["gpu"]["max_tokens"]
GPU_MIN_BATCH = cfg["gpu"]["min_batch"]
GPU_MAX_BATCH = cfg["gpu"]["max_batch"]
GPU_STASH_MAX_AGE_MS = cfg["gpu"]["stash_max_age_ms"]
