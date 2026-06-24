import signal


class SignalHandler:
    def __init__(self, shutdown_callback):
        self.shutdown_callback = shutdown_callback

    def register(self):
        signal.signal(signal.SIGINT, self.shutdown_callback)
        signal.signal(signal.SIGTERM, self.shutdown_callback)
