import logging

from uvicorn.logging import DefaultFormatter


def get_logger(name: str, log_level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(log_level)
        ch = logging.StreamHandler()
        ch.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))
        logger.addHandler(ch)

    return logger
