import sys

from loguru import logger

logger.add(
    sys.stderr,
    format='{{"timestamp":"{time}","level":"{level}","message":"{message}"}}',
    level="INFO",
)


def set_level(level):
    global logger
    logger.remove()
    logger.add(
        sys.stderr,
        format='{{"timestamp":"{time}","level":"{level}","message":"{message}"}}',
        level=level,
    )
