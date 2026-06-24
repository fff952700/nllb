class AppContext:
    """
    全局依赖容器（生产级简化 DI）
    """

    def __init__(self, config):
        self.config = config
        self.redis = None
        self.translator = None
        self.worker_manager = None
