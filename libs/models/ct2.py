import ctranslate2
from transformers import AutoTokenizer


class CT2Model:

    def __init__(self, model_cfg, runtime_cfg):

        self.model_cfg = model_cfg
        self.runtime_cfg = runtime_cfg

        self.model_path = model_cfg.ct2_path
        self.max_length = model_cfg.max_length

        self.device = runtime_cfg.device

        self.translator = None
        self.tokenizer = None

        # DO NOT call _init() here. multiprocessing fork will break the C++ thread pool.
        # It will be lazy loaded in the worker process.

    def load(self):
        if self.translator is not None:
            return

        print(f"[CT2] lazy loading in process, device={self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_cfg.name
        )

        # ⭐ 强制CPU
        if self.device == "cpu":
            self.translator = ctranslate2.Translator(
                self.model_path,
                device="cpu",
                compute_type="int8"
            )
        else:
            self.translator = ctranslate2.Translator(
                self.model_path,
                device="cuda",
                compute_type="float16"
            )

    def translate_batch(self, items):
        if self.translator is None:
            self.load()


        texts = []
        task_ids = []

        first = items[0]

        src_lang = first.get("src_lang") or "eng_Latn"
        tgt_lang = first.get("tgt_lang") or "eng_Latn"

        self.tokenizer.src_lang = src_lang

        for it in items:
            texts.append(it["text"])
            task_ids.append(it["task_id"])

        source = [
            self.tokenizer.convert_ids_to_tokens(
                self.tokenizer.encode(t)
            )
            for t in texts
        ]

        target_prefix = [[tgt_lang]] * len(texts)

        results = self.translator.translate_batch(
            source,
            target_prefix=target_prefix,
            max_decoding_length=self.max_length,
            beam_size=1
        )

        out = {}

        for i, res in enumerate(results):
            tokens = res.hypotheses[0][1:]
            out[task_ids[i]] = self.tokenizer.decode(
                self.tokenizer.convert_tokens_to_ids(tokens)
            )

        return out
