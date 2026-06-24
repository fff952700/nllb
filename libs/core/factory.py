from translators.cpu import CPUTranslator
from translators.gpu import GPUTranslator


class TranslatorFactory:

    def __init__(self, config):
        self.config = config

    def create(self):

        if self.config.runtime.device == "gpu":
            return GPUTranslator()

        return CPUTranslator()
