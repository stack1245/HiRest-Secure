"""유틸리티 함수 모음"""
from __future__ import annotations

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
    """임베드 생성.
    
    Args:
        title: 임베드 제목
        description: 임베드 설명
        color: 임베드 색상
        ctx: 명령어 컨텍스트 (미사용)
        success: 성공/실패 여부에 따른 자동 색상 설정
        
    Returns:
        생성된 Discord 임베드
    """
    if success is True:
        color = EMBED_SUCCESS
    elif success is False:
        color = EMBED_ERROR
    elif color == EMBED_PROCESSING:
        color = EMBED_PROCESSING
    
    return discord.Embed(description=description, color=color, timestamp=datetime.now())


class CommandLogger:
    """명령어 사용 로거 (현재 비활성화)."""
    
    @staticmethod
    async def log_command_usage(
        ctx: discord.ApplicationContext,
        command_name: str,
        parameters: Dict[str, Any],
        success: bool
    ) -> None:
        """명령어 사용 로그 기록 (구현되지 않음)"""
        pass


def validate_minecraft_username(username: str) -> bool:
    """마인크래프트 사용자명 유효성 검증.
    
    Args:
        username: 검증할 사용자명
        
    Returns:
        유효한 사용자명 여부
    """
    if not username or not (3 <= len(username) <= 16):
        return False
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username))


class ConsoleResponseParser:
    """콘솔 응답 파싱 유틸리티."""
    
    @staticmethod
    def parse_player_info(console_output: str) -> Optional[Dict[str, str]]:
        """콘솔 출력에서 플레이어 정보 추출.
        
        Args:
            console_output: 파싱할 콘솔 출력
            
        Returns:
            플레이어 정보 또는 None
        """
        try:
            patterns = {
                'uuid': r'UUID:\s*([a-f0-9-]+)',
                'ip': r'IP:\s*([\d.]+)',
                'group': r'Group:\s*(\w+)',
                'playtime': r'PlayTime:\s*(.+)'
            }
            
            info: Dict[str, str] = {}
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
        """콘솔 출력에서 플레이어 목록 파싱.
        
        Args:
            console_output: 파싱할 콘솔 출력
            
        Returns:
            플레이어 목록 정보
        """
        try:
            data: Dict[str, Any] = {
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
    """콘솔 응답 처리 핸들러."""
    
    def __init__(self, bot: object, console_channel_id: int) -> None:
        """초기화.
        
        Args:
            bot: Discord 봇
            console_channel_id: 콘솔 채널 ID
        """
        self.bot = bot
        self.console_channel_id = console_channel_id
        self.parser = ConsoleResponseParser()
    
    async def wait_for_response(
        self,
        mention: str,
        timeout: float = 5.0,
        keywords: Optional[List[str]] = None
    ) -> Optional[str]:
        """콘솔 채널에서 응답 대기.
        
        Args:
            mention: 언급 (미사용)
            timeout: 타임아웃 (초)
            keywords: 검색 키워드
            
        Returns:
            콘솔 응답 또는 None
        """
        try:
            channel = self.bot.get_channel(self.console_channel_id)
            if not channel:
                logger.error(f"콘솔 채널 없음: {self.console_channel_id}")
                return None
            
            await asyncio.sleep(2.0)
            
            messages = [msg async for msg in channel.history(limit=50)]
            messages.reverse()
            blocks = self._extract_console_blocks(messages)
            
            if blocks:
                return self._find_matching_block(blocks, keywords)
            
            return None
        except Exception as e:
            logger.error(f"콘솔 응답 대기 오류: {e}")
            return None
    
    def _extract_console_blocks(self, messages: List) -> List[str]:
        """메시지에서 콘솔 블록 추출.
        
        Args:
            messages: 메시지 목록
            
        Returns:
            콘솔 블록 목록
        """
        blocks: List[str] = []
        lines: List[str] = []
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
    
    def _find_matching_block(
        self,
        blocks: List[str],
        keywords: Optional[List[str]]
    ) -> Optional[str]:
        """키워드에 맞는 블록 찾기.
        
        Args:
            blocks: 블록 목록
            keywords: 검색 키워드
            
        Returns:
            일치하는 블록 또는 None
        """
        if keywords:
            for block in reversed(blocks):
                if any(keyword.lower() in block.lower() for keyword in keywords):
                    return block
        
        return blocks[-1] if blocks else None


def parse_player_info(console_output: str, player: str) -> Optional[Dict[str, str]]:
    """콘솔 출력에서 플레이어 정보 파싱.
    
    Args:
        console_output: 파싱할 콘솔 출력
        player: 플레이어명
        
    Returns:
        플레이어 정보 또는 None
    """
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