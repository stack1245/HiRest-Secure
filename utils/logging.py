"""로깅 설정"""
from __future__ import annotations
import logging

__all__ = ["configure_logging"]

_SUPPRESS_LOGGERS = (
    "discord",
    "discord.client",
    "discord.gateway",
    "discord.http",
)


def configure_logging(level: int = logging.ERROR) -> None:
    """로깅 설정 및 Discord 라이브러리 로그 억제"""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(message)s")
    
    for logger_name in _SUPPRESS_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
