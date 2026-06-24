class Engine:

    def __init__(self, settings):
        self.settings = settings
        self._services = {}

    def init_stream(self):
        # 确保 redis 连接已绑定
        redis_client = self.get("redis")
        if not redis_client:
            return
            
        try:
            redis_client.client.xgroup_create(
                self.settings.stream.name,
                self.settings.stream.group,
                id="0",
                mkstream=True
            )
        except Exception:
            pass

    def bind(self, name, obj):
        self._services[name] = obj
        setattr(self, name, obj)

    def get(self, name):
        return self._services.get(name)

    def has(self, name):
        return name in self._services
