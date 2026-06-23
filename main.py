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
