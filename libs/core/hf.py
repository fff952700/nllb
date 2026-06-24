import os
from huggingface_hub import login


class HFContext:

    def __init__(self, config):
        self.config = config
        self.token = os.getenv("HF_TOKEN")

    def init(self):
        if self.token:
            login(token=self.token)
