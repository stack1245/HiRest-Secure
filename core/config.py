"""Bot configuration management."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass
except Exception:
    pass


@dataclass
class Config:
    """봇 설정을 관리하는 데이터 클래스."""
    
    DISCORD_TOKEN: str
    TARGET_GUILD_ID: int
    API_REQUEST_CHANNEL_ID: int
    ILUNAR_CONSOLE_CHANNEL_ID: int
    BAN_LOG_CHANNEL_ID: int
    LOG_CHANNEL_ID: int
    STAFF_ROLE_ID: int
    DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    EMBED_FOOTER: str = "HiRest Management Bot"
    
    def __post_init__(self) -> None:
        """Discord 관련 로거 설정."""
        for logger_name in ['discord', 'discord.client', 'discord.gateway', 'discord.http']:
            logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    def validate_config(self) -> bool:
        """필수 설정 항목이 모두 존재하는지 검증."""
        required_fields = [
            'DISCORD_TOKEN', 'TARGET_GUILD_ID', 'STAFF_ROLE_ID',
            'API_REQUEST_CHANNEL_ID', 'ILUNAR_CONSOLE_CHANNEL_ID', 'BAN_LOG_CHANNEL_ID'
        ]
        missing = [field for field in required_fields if not getattr(self, field, None)]
        
        if missing:
            logging.error(f"필수 설정 누락: {', '.join(missing)}")
        return not missing


def get_config() -> Config:
    """환경 변수에서 설정을 로드하여 Config 객체 생성."""
    
    def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
        value = os.getenv(key)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_bool(key: str, default: bool = False) -> bool:
        return os.getenv(key, "").lower() in ("true", "1", "yes", "on")

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN 미설정")

    api_channel = get_int("API_REQUEST_CHANNEL_ID")
    console_channel = get_int("ILUNAR_CONSOLE_CHANNEL_ID") or get_int("CONSOLE_CHANNEL_ID")
    ban_log_channel = get_int("BAN_LOG_CHANNEL_ID")
    log_channel = get_int("LOG_CHANNEL_ID") or api_channel

    return Config(
        DISCORD_TOKEN=token,
        TARGET_GUILD_ID=get_int("TARGET_GUILD_ID", 0),
        API_REQUEST_CHANNEL_ID=api_channel or 0,
        ILUNAR_CONSOLE_CHANNEL_ID=console_channel or 0,
        BAN_LOG_CHANNEL_ID=ban_log_channel or 0,
        LOG_CHANNEL_ID=log_channel or 0,
        STAFF_ROLE_ID=get_int("STAFF_ROLE_ID", 0),
        DEBUG_MODE=get_bool("DEBUG_MODE"),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        EMBED_FOOTER=os.getenv("EMBED_FOOTER", "HiRest Management Bot")
    )