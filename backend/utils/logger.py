import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(app):
    """Set up console + rotating file logging once during app startup."""

    log_dir = Path(app.config['LOG_DIR'])
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'application.log'

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    if not any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(file_handler)

    for handler in app.logger.handlers:
        handler.setFormatter(formatter)

    app.logger.setLevel(app.config['LOG_LEVEL'])
    app.logger.propagate = False
    app.logger.info('Logging configured for %s environment.', app.config['APP_ENV'])
    return app.logger
