from redis_client import redis_client
from settings import RL_ENABLED, RL_LIMIT, RL_WINDOW


def rate_limit(api_key: str, route: str = "translate"):

    if not RL_ENABLED:
        return True

    key = f"rl:{api_key}:{route}"

    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, RL_WINDOW)

    return count <= RL_LIMIT
