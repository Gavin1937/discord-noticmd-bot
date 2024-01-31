import logging
import logging.config

__all__ = [
    "logger"
]

loggerName = "discord-noticmd-bot"
loggerLevel = "DEBUG"
logFile = "./discord-noticmd-bot.log"
logFormatStr = "[%(levelname)s][%(asctime)s]:%(funcName)s - %(message)s"

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": logFormatStr
        },
        "file": {
            "format": logFormatStr
        }
    },
    "handlers": {
        "console_handler": {
            "class": "logging.StreamHandler",
            "level": loggerLevel,
            "formatter": "console",
            "stream": "ext://sys.stdout"
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": loggerLevel,
            "formatter": "file",
            "filename": logFile,
            "maxBytes": 5*1024*1024,
            "backupCount": 10,
        }
    },
    "loggers": {
        loggerName: {
            "handlers": ["console_handler", "file_handler"],
            "level": loggerLevel
        }
    }
}

logging.config.dictConfig(config=logging_config)
logger = logging.getLogger(loggerName)

