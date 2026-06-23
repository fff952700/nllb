import ctranslate2
from transformers import AutoTokenizer

from settings import MODEL_NAME, CT2_PATH, MAX_LENGTH


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


def norm(lang):
    return LANG_MAP.get(lang, lang)


# 延迟加载，防止多进程 fork 导致的 C++ 线程池死锁问题
translator = None
tokenizer = None

def get_models():
    global translator, tokenizer
    if translator is None:
        print("Initializing HuggingFace Tokenizer...", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("Initializing CTranslate2 Translator on CPU...", flush=True)
        translator = ctranslate2.Translator(CT2_PATH, device="cpu", compute_type="int8")
        print("Initialization completed.", flush=True)
    return tokenizer, translator

def translate_batch_grouped(items):
    print(f"Entering translate_batch_grouped for {len(items)} tasks...", flush=True)
    tok, trans = get_models()

    texts = []
    task_ids = []

    src_lang = norm(items[0]["src_lang"])
    tgt_lang = norm(items[0]["tgt_lang"])

    tok.src_lang = src_lang

    for it in items:
        texts.append(it["text"])
        task_ids.append(it["task_id"])

    # 1. 转换为 Token 列表
    source = [tok.convert_ids_to_tokens(tok.encode(t)) for t in texts]

    # 2. 设置目标语言的 prefix
    target_prefix = [[tgt_lang]] * len(texts)

    # 3. 批量推理
    print(f"Calling trans.translate_batch for {len(texts)} sentences...", flush=True)
    results = trans.translate_batch(
        source,
        target_prefix=target_prefix,
        max_decoding_length=MAX_LENGTH,
        beam_size=1
    )

    # 4. 解码 Token 列表为字符串
    decoded = []
    for res in results:
        # res.hypotheses[0] 包含了 [tgt_lang_token, token1, token2, ...]
        # 我们用 [1:] 去掉开头的语言标识符，避免出现在翻译文本中
        target_tokens = res.hypotheses[0][1:]
        text = tok.decode(tok.convert_tokens_to_ids(target_tokens))
        decoded.append(text)

    return dict(zip(task_ids, decoded))
