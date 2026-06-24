import os
from huggingface_hub import login


class HFClient:

    def __init__(self, cfg):
        self.cfg = cfg

    def init(self):

        token = self.cfg.get("token")

        if token:
            login(token=token)

        os.environ["HF_HOME"] = self.cfg.get("cache_dir", "/tmp/hf")
