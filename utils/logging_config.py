import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app):
    Path("logs").mkdir(exist_ok=True)

    handler = RotatingFileHandler(
        "logs/saivex.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("SAIVEX production logging started")
