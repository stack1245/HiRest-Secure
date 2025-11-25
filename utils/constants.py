"""Constants and predefined options."""
from typing import List
import discord

__all__ = [
    "COLORS",
    "DEFAULT_ACTIVITY_NAME",
    "AUTO_SAVE_INTERVAL",
    "COMMAND_DELAY",
    "PROCESSING_DELAY",
    "INFO_DELAY",
    "CONSOLE_RESPONSE_DELAY",
    "TEMPBAN_DURATION_OPTIONS",
    "TEMPBAN_REASON_OPTIONS",
    "BAN_REASON_OPTIONS",
    "MUTE_DURATION_OPTIONS",
    "MUTE_REASON_OPTIONS",
    "KICK_REASON_OPTIONS",
]

COLORS = {
    "ERROR": 0xE74C3C,
    "SUCCESS": 0x2ECC71,
    "INFO": 0x3498DB,
    "NEUTRAL": 0x95A5A6,
    "QUEUE": 0x3498DB,
    "KARAOKE": 0x9B59B6,
}

DEFAULT_ACTIVITY_NAME: str = "HiRest Secure"
AUTO_SAVE_INTERVAL: int | None = None

COMMAND_DELAY = 1
PROCESSING_DELAY = 1
INFO_DELAY = 3
CONSOLE_RESPONSE_DELAY = 5

TEMPBAN_DURATION_OPTIONS: List[str] = [
    "30m", "1h", "2h", "3h", "6h", "12h",
    "1d", "2d", "3d", "6d", "7d", "9d", "15d", "45d", "영구"
]

TEMPBAN_REASON_OPTIONS: List[str] = [
    "1-5: 허위 사실 유포 (7일)",
    "1-11: 무단 홍보 (7일)",
    "2-4: 부적절한 닉네임/스킨 사용 (변경 전까지)",
    "2-5: 서버 내 렉머신 (7일)",
    "2차 처벌: 허위 사실 유포 (21일)",
    "2차 처벌: 무단 홍보 (21일)",
    "2차 처벌: 부적절한 닉네임/스킨 (변경 전까지)",
    "2차 처벌: 렉머신 (21일)",
    "이용약관 위반",
    "관리진 재량",
    "기타"
]

BAN_REASON_OPTIONS: List[str] = [
    "1-3: 타인의 개인정보 유포",
    "1-6: 서버 분위기 저하성 발언",
    "1-7: 서버 비하",
    "1-9: 관리진 사칭",
    "1-10: 허위 진술·증거 인멸/조작 행위",
    "2-1: 비인가 프로그램 및 모드 사용",
    "2-2: IP 우회(VPN/Proxy)",
    "2-3: 특정 목적 부계정 사용",
    "2-6: 부적절한 거래 (현금거래/사기)",
    "2-7: 버그 악용",
    "2-8: 약탈 및 테러 (Arsenic 제외)",
    "2-9: 합의되지 않은 PvP (Arsenic 제외)",
    "3-1: 티켓 내 무례한 언행",
    "3-2: 운영 간섭 및 조치 강요",
    "3차 처벌: Strike-Out 제도",
    "중대한 약관 위반",
    "관리진 재량",
    "기타"
]

MUTE_DURATION_OPTIONS: List[str] = [
    "30s", "30m", "1h", "3h", "6h", "18h", "1d", "permanent", "영구"
]

MUTE_REASON_OPTIONS: List[str] = [
    "1-1: 부적절한 언행 (비대상, 2시간)",
    "1-1: 부적절한 언행 (특정 유저 대상, 12시간)",
    "1-2: 채팅 도배 (실수, 30분)",
    "1-2: 채팅 도배 (고의, 1시간)",
    "1-4: 분쟁 유도 (12시간)",
    "1-4: 분쟁 (관련자 모두, 2일)",
    "1-8: 혐오 컨텐츠 유포 (6시간)",
    "2차 처벌: 부적절한 언행 (비대상, 6시간)",
    "2차 처벌: 부적절한 언행 (특정 유저, 36시간)",
    "2차 처벌: 도배 (실수, 90분)",
    "2차 처벌: 도배 (고의, 3시간)",
    "2차 처벌: 분쟁 유도 (36시간)",
    "2차 처벌: 분쟁 (관련자 모두, 6일)",
    "2차 처벌: 혐오 컨텐츠 (18시간)",
    "채팅 규칙 위반",
    "관리진 재량",
    "기타"
]

KICK_REASON_OPTIONS: List[str] = [
    "경고: 약관 위반 근접",
    "경고: 경미한 규칙 위반",
    "경고: 채팅 규칙 위반",
    "경고: 인게임 규칙 위반",
    "AFK (자리비움)",
    "서버 과부하 방지",
    "접속 오류 해결",
    "관리진 재량",
    "기타"
]


def _create_autocomplete(options: List[str]):
    async def autocomplete(ctx: discord.AutocompleteContext):
        return [opt for opt in options if ctx.value.lower() in opt.lower()][:25]
    return autocomplete


tempban_duration_autocomplete = _create_autocomplete(TEMPBAN_DURATION_OPTIONS)
tempban_reason_autocomplete = _create_autocomplete(TEMPBAN_REASON_OPTIONS)
ban_reason_autocomplete = _create_autocomplete(BAN_REASON_OPTIONS)
mute_duration_autocomplete = _create_autocomplete(MUTE_DURATION_OPTIONS)
mute_reason_autocomplete = _create_autocomplete(MUTE_REASON_OPTIONS)
kick_reason_autocomplete = _create_autocomplete(KICK_REASON_OPTIONS)

__all__ = [
    "COLORS",
    "DEFAULT_ACTIVITY_NAME",
    "AUTO_SAVE_INTERVAL",
    "TEMPBAN_DURATION_OPTIONS",
    "TEMPBAN_REASON_OPTIONS",
    "BAN_REASON_OPTIONS",
    "MUTE_DURATION_OPTIONS",
    "MUTE_REASON_OPTIONS",
    "KICK_REASON_OPTIONS",
    "tempban_duration_autocomplete",
    "tempban_reason_autocomplete",
    "ban_reason_autocomplete",
    "mute_duration_autocomplete",
    "mute_reason_autocomplete",
    "kick_reason_autocomplete",
]
