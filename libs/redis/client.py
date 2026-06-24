import redis


class RedisClient:

    def __init__(self, cfg):

        self.client = redis.Redis(
            host=cfg.host,
            port=cfg.port,
            db=cfg.db,
            password=cfg.password,
            decode_responses=True,
            max_connections=cfg.max_connections
        )

    def get(self, k):
        return self.client.get(k)

    def set(self, k, v, ex=None):
        return self.client.set(k, v, ex=ex)

    def publish(self, ch, msg):
        return self.client.publish(ch, msg)

    def xadd(self, stream, data):
        return self.client.xadd(stream, data)

    def xack(self, stream, group, msg_id):
        return self.client.xack(stream, group, msg_id)

    def xreadgroup(self, group, consumer, streams, count=10, block=1000):
        return self.client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams=streams,
            count=count,
            block=block
        )
