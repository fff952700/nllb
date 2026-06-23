import redis
from settings import *

pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD or None,
    decode_responses=True,
    max_connections=REDIS_MAX_CONN
)

redis_client = redis.Redis(connection_pool=pool)
