import signal
import sys
from typing import List

from service.base import BaseWorker


class WorkerManager:
    """统一管理所有 Worker 的生命周期"""

    def __init__(self):
        self._workers: List[BaseWorker] = []

    def add_worker(self, worker: BaseWorker) -> None:
        self._workers.append(worker)

    def start_all(self) -> None:
        print(f"[WorkerManager] starting {len(self._workers)} worker(s)...", flush=True)
        for worker in self._workers:
            worker.start()
        print("[WorkerManager] all workers started.", flush=True)

        # 注册信号处理，确保 Ctrl+C 时优雅停止
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def stop_all(self) -> None:
        print("[WorkerManager] stopping all workers...", flush=True)
        for worker in self._workers:
            worker.stop()
        print("[WorkerManager] all workers stopped.", flush=True)

    def _handle_shutdown(self, signum, frame):
        print(f"\n[WorkerManager] received signal {signum}, shutting down...", flush=True)
        self.stop_all()
        sys.exit(0)
