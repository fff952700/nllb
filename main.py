import uvicorn
from settings import HOST, PORT

LOG_FILE = "/data/nllb/logs/uvicorn.log"

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "access": {
            "format": "%(asctime)s [ACCESS] %(message)s"
        }
    },

    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "default"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        }
    },

    "loggers": {
        "uvicorn": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["file", "console"],
            "level": "INFO"
        },
        "uvicorn.access": {
            "handlers": ["file", "console"],
            "level": "INFO"
        }
    },

    "root": {
        "handlers": ["file", "console"],
        "level": "INFO"
    }
}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        workers=1,
        loop="uvloop",
        log_config=LOG_CONFIG,
        access_log=True
    )


# main.py
from config.build import build_settings
from worker.manager import WorkerManager
from service.cpu_service import CPUService
from service.gpu_service import GPUService
from model.translator import Translator

def create_app(config_path: str):

    # 1. config
    settings = build_settings(config_path)

    # 2. model
    translator = Translator()

    # 3. service
    cpu_service = CPUService(translator, settings.cpu)
    gpu_service = GPUService(translator, settings.gpu)

    # 4. worker manager
    manager = WorkerManager()

    manager.add_worker(cpu_service)
    manager.add_worker(gpu_service)

    manager.start_all()

    return {
        "settings": settings,
        "cpu": cpu_service,
        "gpu": gpu_service,
        "workers": manager,
    }


if __name__ == "__main__":
    app = create_app("conf/config.yaml")
