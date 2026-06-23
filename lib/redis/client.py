import redis
from conf.setting import RedisConfig


class RedisClient:
    """Redis 客户端封装，接受 RedisConfig，不依赖全局 settings"""

    def __init__(self, cfg: RedisConfig):
        pool = redis.ConnectionPool(
            host=cfg.host,
            port=cfg.port,
            db=cfg.db,
            password=cfg.password or None,
            decode_responses=True,
            max_connections=cfg.max_connections,
        )
        self._client = redis.Redis(connection_pool=pool)

    def __getattr__(self, name: str):
        """将所有方法调用代理给底层 redis.Redis 实例"""
        return getattr(self._client, name)
