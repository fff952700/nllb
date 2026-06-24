class WorkerManager:

    def __init__(self):
        self.workers = []

    def add(self, worker):
        self.workers.append(worker)

    def start(self):
        for w in self.workers:
            w.start()

    def stop(self):
        for w in self.workers:
            w.terminate()
