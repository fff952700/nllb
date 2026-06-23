import abc
from typing import List, Dict, Any


class BaseTranslator(abc.ABC):
    """翻译器抽象基类，CPU/GPU 实现均继承此类"""

    @abc.abstractmethod
    def translate_batch(self, items: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        批量翻译。
        :param items: 任务列表，每项包含 task_id, text, src_lang, tgt_lang
        :return: {task_id: translated_text} 映射
        """
        pass


class BaseWorker(abc.ABC):
    """Worker 抽象基类，负责从 Redis 流读取任务并调用 translator 处理"""

    def __init__(self, translator: BaseTranslator, redis_client, stream_cfg, worker_cfg):
        self.translator = translator
        self.redis = redis_client
        self.stream_cfg = stream_cfg
        self.worker_cfg = worker_cfg

    @abc.abstractmethod
    def start(self) -> None:
        """启动 worker（多进程/多线程）"""
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        """停止所有 worker"""
        pass
