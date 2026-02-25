from loguru import logger
import sys
from .settings import settings

def configure_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, enqueue=True, backtrace=False, diagnose=False)
