from typing import List, Dict, Any

import ctranslate2
from transformers import AutoTokenizer

from conf.setting import ModelConfig
from service.base import BaseTranslator


LANG_MAP = {
    "en": "eng_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "ru": "rus_Cyrl",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "zh": "zho_Hans",
}


def _norm(lang: str) -> str:
    return LANG_MAP.get(lang, lang)


class GPUTranslator(BaseTranslator):
    """基于 CTranslate2（CUDA int8_float16）的翻译器，懒加载模型防止多进程 fork 死锁"""

    def __init__(self, cfg: ModelConfig):
        self._cfg = cfg
        self._tokenizer = None
        self._translator = None

    def _load(self):
        """懒加载：在 worker 进程内首次调用时才初始化模型"""
        if self._translator is None:
            print("GPUTranslator: Initializing tokenizer...", flush=True)
            self._tokenizer = AutoTokenizer.from_pretrained(self._cfg.name)
            print("GPUTranslator: Initializing CTranslate2 (CUDA, int8_float16)...", flush=True)
            self._translator = ctranslate2.Translator(
                self._cfg.ct2_path,
                device="cuda",
                compute_type="int8_float16",
            )
            print("GPUTranslator: Ready.", flush=True)

    def translate_batch(self, items: List[Dict[str, Any]]) -> Dict[str, str]:
        self._load()

        tok = self._tokenizer
        trans = self._translator

        src_lang = _norm(items[0]["src_lang"])
        tgt_lang = _norm(items[0]["tgt_lang"])
        tok.src_lang = src_lang

        texts = [it["text"] for it in items]
        task_ids = [it["task_id"] for it in items]

        # Token 化
        source = [tok.convert_ids_to_tokens(tok.encode(t)) for t in texts]
        target_prefix = [[tgt_lang]] * len(texts)

        # 批量推理
        results = trans.translate_batch(
            source,
            target_prefix=target_prefix,
            max_decoding_length=self._cfg.max_length,
            beam_size=1,
        )

        # 解码
        decoded = []
        for res in results:
            target_tokens = res.hypotheses[0][1:]  # 去掉开头的语言标识符
            text = tok.decode(tok.convert_tokens_to_ids(target_tokens))
            decoded.append(text)

        return dict(zip(task_ids, decoded))
