import ast
import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from project_title.settings import LOG_DIR

from tools.datetimes import jdt

PROCESS_TYPE = os.getenv("PROCESS_TYPE", "django")

LOG_PATH = f"{LOG_DIR}/django/{PROCESS_TYPE}"


class JsonFormatter(logging.Formatter):
    """Structured JSON Formatter for ELK"""

    def format(self, record: logging.LogRecord) -> str:

        # Parse message
        try:
            details = ast.literal_eval(record.getMessage())
        except SyntaxError:
            details = record.getMessage()

        # Data
        log_record = {
            "@timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "jalali_datetime": jdt.datetime.fromgregorian(
                datetime=datetime.fromtimestamp(record.created)
            ).isoformat()
            + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "file": record.filename,
            "line": record.lineno,
            "process": PROCESS_TYPE,
        }

        if record.exc_info:
            log_record["error_title"] = record.exc_info[0].__name__
            log_record["error_message"] = str(record.exc_info[1])

        if isinstance(details, dict):
            log_record["extra"] = details
            log_record["message"] = None
        else:
            log_record["message"] = details
            log_record["extra"] = None

        return json.dumps(log_record, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable formatter"""

    def __init__(self):
        super().__init__(
            "[%(asctime)s] [%(levelname)s] [%(name)s] "
            "(%(filename)s:%(lineno)d) → %(message)s"
        )


def logger_set(app: str) -> logging.Logger:
    """Create a logger with JSON and Text file handlers"""
    logger = logging.getLogger(app)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    # JSON file handler
    json_handler = RotatingFileHandler(
        LOG_PATH + ".json.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    json_handler.setFormatter(JsonFormatter())
    json_handler.setLevel(logging.INFO)

    # Text file handler
    text_handler = RotatingFileHandler(
        LOG_PATH + ".log",
        maxBytes=50 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    text_handler.setFormatter(TextFormatter())
    text_handler.setLevel(logging.INFO)

    logger.addHandler(json_handler)
    logger.addHandler(text_handler)

    return logger
