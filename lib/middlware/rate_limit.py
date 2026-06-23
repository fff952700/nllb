from conf.setting import RateLimitConfig
from lib.redis.client import RedisClient


class RateLimiter:
    """速率限制器，接受 RedisClient 和 RateLimitConfig，不依赖全局 settings"""

    def __init__(self, redis_client: RedisClient, cfg: RateLimitConfig):
        self._redis = redis_client
        self._cfg = cfg

    def check(self, api_key: str, route: str = "translate") -> bool:
        """返回 True 表示允许通过，False 表示已超出限额"""
        if not self._cfg.enabled:
            return True

        key = f"rl:{api_key}:{route}"
        count = self._redis.incr(key)

        if count == 1:
            self._redis.expire(key, self._cfg.window)

        return count <= self._cfg.limit
