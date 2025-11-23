import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import discord

EMBED_SUCCESS = 0x27AE60
EMBED_ERROR = 0xE74C3C
EMBED_INFO = 0x0099FF
EMBED_PROCESSING = 0xF39C12

logger = logging.getLogger(__name__)


def create_embed(
    title: str,
    description: str,
    color: int = EMBED_INFO,
    ctx: Optional[discord.ApplicationContext] = None,
    success: Optional[bool] = None
) -> discord.Embed:
    if success is True:
        color = EMBED_SUCCESS
    elif success is False:
        color = EMBED_ERROR
    elif color == EMBED_PROCESSING:
        color = EMBED_PROCESSING
    
    return discord.Embed(description=description, color=color, timestamp=datetime.now())


class CommandLogger:
    @staticmethod
    async def log_command_usage(
        ctx: discord.ApplicationContext,
        command_name: str,
        parameters: Dict[str, Any],
        success: bool
    ) -> None:
        pass


def validate_minecraft_username(username: str) -> bool:
    if not username or not (3 <= len(username) <= 16):
        return False
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username))


class ConsoleResponseParser:
    @staticmethod
    def parse_player_info(console_output: str) -> Optional[Dict[str, str]]:
        try:
            patterns = {
                'uuid': r'UUID:\s*([a-f0-9-]+)',
                'ip': r'IP:\s*([\d.]+)',
                'group': r'Group:\s*(\w+)',
                'playtime': r'PlayTime:\s*(.+)'
            }
            
            info = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, console_output, re.IGNORECASE)
                if match:
                    info[key] = match.group(1).strip() if key == 'playtime' else match.group(1)
            
            return info if info else None
        except Exception as e:
            logger.error(f"파싱 오류: {e}")
            return None
    
    @staticmethod
    def parse_player_list(console_output: str) -> Dict[str, Any]:
        try:
            data = {
                "total_players": 0, "max_players": 999,
                "special": [], "default": [], "premium": [], "lite": [],
                "ultra": [], "booster": [], "youtuber": [], "mod": [],
                "admin": [], "owner": []
            }
            
            for line in console_output.split('\n'):
                clean_line = re.sub(r'\[.*?\s+\d+:\d+:\d+\s+INFO\s*\]\s*', '', line).strip()
                
                if not clean_line or "========================" in clean_line:
                    continue
                
                if "Players online" in clean_line:
                    match = re.search(r'Players online (\d+)/(\d+)', clean_line)
                    if match:
                        data['total_players'] = int(match.group(1))
                        data['max_players'] = int(match.group(2))
                    continue
                
                rank_match = re.match(r'^(\w+):\s*(.+)$', clean_line)
                if rank_match:
                    rank = rank_match.group(1).lower()
                    players_str = rank_match.group(2).strip()
                    
                    if rank in data and players_str:
                        players = [p.strip() for p in players_str.split(',') if p.strip()]
                        data[rank].extend(players)
            
            return data
        except Exception as e:
            logger.error(f"목록 파싱 오류: {e}")
            return {"total_players": 0, "max_players": 999, "message": f"파싱 오류: {e}"}


class ConsoleResponseHandler:
    def __init__(self, bot, console_channel_id: int) -> None:
        self.bot = bot
        self.console_channel_id = console_channel_id
        self.parser = ConsoleResponseParser()
    
    async def wait_for_response(
        self, mention: str, timeout: float = 5.0, keywords: Optional[List[str]] = None
    ) -> Optional[str]:
        try:
            channel = self.bot.get_channel(self.console_channel_id)
            if not channel:
                logger.error(f"[HiRest Secure] 콘솔 채널 없음: {self.console_channel_id}")
                return None
            
            await asyncio.sleep(2.0)
            
            messages = [msg async for msg in channel.history(limit=50)]
            messages.reverse()
            blocks = self._extract_console_blocks(messages)
            
            if blocks:
                return self._find_matching_block(blocks, keywords)
            
            logger.warning(f"[HiRest Secure] 콘솔 응답 없음: {mention}")
            return None
        except Exception as e:
            logger.error(f"[HiRest Secure] 콘솔 응답 대기 오류: {e}")
            return None
    
    def _extract_console_blocks(self, messages: List) -> List[str]:
        blocks = []
        lines = []
        in_block = False
        separators = ["========================", "--------------------------------------------------"]
        
        for msg in messages:
            for line in msg.content.split('\n'):
                if any(sep in line for sep in separators):
                    if in_block and lines:
                        blocks.append('\n'.join(lines))
                    lines = []
                    in_block = not in_block
                elif in_block:
                    lines.append(line)
        
        return blocks
    
    def _find_matching_block(self, blocks: List[str], keywords: Optional[List[str]]) -> Optional[str]:
        if keywords:
            for block in reversed(blocks):
                if any(keyword.lower() in block.lower() for keyword in keywords):
                    return block
        
        return blocks[-1] if blocks else None


def parse_player_info(console_output: str, player: str) -> Optional[Dict[str, str]]:
    """콘솔 출력에서 플레이어 정보 파싱."""
    try:
        logger.debug(f"원본 콘솔 출력 (첫 500자):\n{console_output[:500]}")
        
        # 원본 텍스트를 줄 단위로 분리 (정리 전)
        raw_lines = console_output.split('\n')
        
        # 타임스탬프만 제거하고 원본 유지
        cleaned_lines = []
        for line in raw_lines:
            # 타임스탬프 패턴 제거: [일 10:57:46 INFO]
            cleaned = re.sub(r'\[.*?\s+\d+:\d+:\d+\s+INFO\s*\]\s*', '', line)
            if cleaned.strip() and not re.match(r'^[-=]{10,}$', cleaned.strip()):
                cleaned_lines.append(cleaned)
        
        # 전체 텍스트 재구성
        full_text = '\n'.join(cleaned_lines)
        logger.debug(f"정리된 출력 (첫 500자):\n{full_text[:500]}")
        
        # === 플레이어 이름 추출 ===
        username = None
        display_name = None
        
        # 패턴 1: "닉네임 Prefix: Suffix: Offline for:" 형식
        # 첫 번째 단어가 플레이어 이름
        first_line = cleaned_lines[0] if cleaned_lines else ""
        if first_line:
            # Prefix: 앞의 첫 단어 추출
            words = first_line.split()
            if words:
                username = words[0]
                logger.debug(f"첫 줄에서 이름 추출: {username}")
        
        # 패턴 2: "username Prefix: x Suffix: y" 형식에서 추출
        if not username:
            name_match = re.search(r'^(\S+)\s+Prefix:', full_text, re.MULTILINE)
            if name_match:
                username = name_match.group(1)
                logger.debug(f"Prefix 패턴에서 이름 추출: {username}")
        
        # 패턴 3: 전통적인 Display name 패턴
        if not username:
            name_match = re.search(r'(\S+)\s+Display name:\s*(\S+)', full_text)
            if name_match:
                username = name_match.group(1)
                display_name = name_match.group(2)
                logger.debug(f"Display name 패턴에서 추출: {username}, {display_name}")
        
        if not username:
            logger.warning(f"플레이어 이름 추출 실패. 첫 줄: {first_line[:100]}")
            return None
        
        # 이름 검증
        player_lower = player.lower()
        username_lower = username.lower()
        if player_lower not in username_lower and username_lower not in player_lower:
            logger.warning(f"이름 불일치: 입력={player}, 추출={username}")
        
        # === UUID 추출 ===
        uuid_value = None
        
        # UUID는 정확한 형식으로만 추출 (36자 또는 32자)
        uuid_patterns = [
            # 표준 UUID (하이픈 포함): 8-4-4-4-12
            r'\bUUID:\s*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
            # 하이픈 없는 UUID
            r'\bUUID:\s*([a-f0-9]{32})\b',
        ]
        
        for pattern in uuid_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                uuid_value = match.group(1)
                logger.info(f"[HiRest Secure] UUID 추출: {uuid_value}")
                break
        
        if not uuid_value:
            logger.warning(f"[HiRest Secure] UUID 미발견: {player}")
            # UUID 라인 전체 출력해서 디버깅
            for line in cleaned_lines:
                if 'UUID' in line.upper():
                    logger.debug(f"UUID 포함 라인: {line}")
        
        # === IP 추출 ===
        ip_value = None
        
        # IP는 정확한 IPv4 형식으로만 추출
        ip_pattern = r'\bIp:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        
        match = re.search(ip_pattern, full_text, re.IGNORECASE)
        if match:
            ip_full = match.group(1)
            # IP 유효성 검사
            ip_parts = ip_full.split('.')
            if len(ip_parts) == 4 and all(0 <= int(p) <= 255 for p in ip_parts):
                # 마지막 옥텏 마스킹
                ip_value = f"{'.'.join(ip_parts[:3])}.*"
                logger.info(f"[HiRest Secure] IP 추출 (마스킹): {ip_value}")
            else:
                logger.warning(f"유효하지 않은 IP: {ip_full}")
        
        if not ip_value:
            logger.warning(f"[HiRest Secure] IP 미발견: {player}")
            # IP 라인 전체 출력해서 디버깅
            for line in cleaned_lines:
                if 'IP' in line.upper():
                    logger.debug(f"IP 포함 라인: {line}")
        
        # === 온라인 상태 ===
        status = "알 수 없음"
        if "Online for:" in full_text or "CanFly" in full_text:
            status = "온라인"
        elif "Offline for:" in full_text:
            status = "오프라인"
        
        # === 결과 구성 ===
        player_info = {
            "username": username,
            "display_name": display_name if display_name and display_name != username else None,
            "status": status
        }
        
        if uuid_value:
            player_info["uuid"] = uuid_value
        else:
            logger.error(f"[HiRest Secure] UUID 추출 실패: {player}")
        
        if ip_value:
            player_info["ip"] = ip_value
        else:
            logger.error(f"[HiRest Secure] IP 추출 실패: {player}")
        
        logger.info(
            f"[HiRest Secure] 파싱 완료: {username} | "
            f"UUID: {'O' if uuid_value else 'X'} | "
            f"IP: {'O' if ip_value else 'X'}"
        )
        
        return player_info
        
    except Exception as e:
        logger.error(f"파싱 예외: {e}", exc_info=True)
        return None