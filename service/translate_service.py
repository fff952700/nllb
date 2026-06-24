import time
import uuid


def process_translation(engine, text: str, src_lang: str, tgt_lang: str):
    task_id = str(uuid.uuid4())

    # NLLB lang code mapping
    lang_map = {
        "zh": "zho_Hans",     # 简体中文
        "zh-tw": "zho_Hant",  # 繁体中文
        "en": "eng_Latn",     # 英语
        "fr": "fra_Latn",     # 法语
        "ar": "arb_Arab",     # 阿拉伯语
        "th": "tha_Thai",     # 泰语
        "es": "spa_Latn",     # 西班牙语
        "de": "deu_Latn",     # 德语
        "ja": "jpn_Jpan",     # 日语
        "ko": "kor_Hang",     # 韩语
        "ru": "rus_Cyrl",     # 俄语
        "pt": "por_Latn",     # 葡萄牙语
        "it": "ita_Latn",     # 意大利语
        "vi": "vie_Latn",     # 越南语
        "id": "ind_Latn",     # 印尼语
    }
    src_lang = lang_map.get(src_lang, src_lang)
    tgt_lang = lang_map.get(tgt_lang, tgt_lang)

    pubsub = engine.redis.client.pubsub()
    pubsub.subscribe(f"notify:{task_id}")

    engine.redis.xadd(
        engine.settings.stream.name,
        {
            "task_id": task_id,
            "text": text,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
        }
    )

    # 同步等待结果，最多等待 30 秒
    timeout = 10
    start_time = time.time()
    result_text = None

    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
        if message:
            result_text = message['data']
            if isinstance(result_text, bytes):
                result_text = result_text.decode('utf-8')
            break

        if time.time() - start_time > timeout:
            break

    pubsub.unsubscribe(f"notify:{task_id}")

    if result_text is not None:
        return {"task_id": task_id, "result": result_text}
    else:
        # 如果 pubsub 没收到，去 redis 再查一下作为 fallback
        cached_result = engine.redis.get(f"result:{task_id}")
        if cached_result:
            if isinstance(cached_result, bytes):
                cached_result = cached_result.decode('utf-8')
            return {"task_id": task_id, "result": cached_result}

        return {"task_id": task_id, "error": "timeout"}
