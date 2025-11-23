import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 1000
MAX_DISPLAY_LOGS = 5

BAN_LOG_PATTERN = "## <:hr_ban:1350451179683057764> 차단 로그"

LogEntry = Dict[str, Any]


async def execute_searchbanlog_action(
    player: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> List[LogEntry]:
    from core.config import get_config
    
    config = get_config()
    
    try:
        # 길드 및 채널 확인
        guild = bot.get_guild(config.TARGET_GUILD_ID)
        if not guild:
            logger.error(f"길드를 찾을 수 없습니다: {config.TARGET_GUILD_ID}")
            return []
        
        ban_log_channel = guild.get_channel(config.BAN_LOG_CHANNEL_ID)
        if not ban_log_channel:
            logger.error(f"차단 로그 채널을 찾을 수 없습니다: {config.BAN_LOG_CHANNEL_ID}")
            return []
        
        found_messages = []
        
        # 메시지 검색
        async for message in ban_log_channel.history(limit=MAX_SEARCH_LIMIT):
            if _is_target_ban_log(message, player):
                log_entry = _create_log_entry(message)
                found_messages.append(log_entry)
        
        # 생성일시 기준 내림차순 정렬 (최신순)
        found_messages.sort(key=lambda x: x["created_at"], reverse=True)
        
        return found_messages
        
    except Exception as e:
        logger.error(f"차단 로그 검색 중 오류 발생: {e}")
        return []


def _is_target_ban_log(message: discord.Message, player: str) -> bool:
    if not message.content:
        return False
        
    # 차단 로그 패턴 확인
    if BAN_LOG_PATTERN not in message.content:
        return False
    
    # 플레이어명 확인 (백틱으로 감싸진 형태)
    return f"`{player}`" in message.content


def _create_log_entry(message: discord.Message) -> LogEntry:
    return {
        "content": message.content,
        "jump_url": message.jump_url,
        "created_at": message.created_at,
        "message_id": message.id,
        "author": message.author.display_name if message.author else "Unknown"
    }


def _create_permission_error_embed(ctx: discord.ApplicationContext) -> discord.Embed:
    """
    권한 부족 오류 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        
    Returns:
        discord.Embed: 권한 오류 임베드
    """
    return create_embed(
        title="❌ 권한 부족",
        description="이 명령어를 사용할 권한이 없습니다.\n**필요 권한**: `스탭`",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_processing_embed(ctx: discord.ApplicationContext, player: str) -> discord.Embed:
    """
    처리 중 상태 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        player: 검색할 플레이어명
        
    Returns:
        discord.Embed: 처리 중 임베드
    """
    return create_embed(
        title="🔍 로그 검색 중...",
        description=f"**`{player}`**님의 차단 로그를 검색하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_search_result_embed(
    ctx: discord.ApplicationContext,
    player: str,
    ban_logs: List[LogEntry]
) -> discord.Embed:
    """
    검색 결과 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        player: 검색한 플레이어명
        ban_logs: 찾은 차단 로그 목록
        
    Returns:
        discord.Embed: 검색 결과 임베드
    """
    if not ban_logs:
        return create_embed(
            title="🔍 차단 로그 검색 결과",
            description=f"**`{player}`**님의 차단 로그를 찾을 수 없습니다.",
            color=0x95A5A6,
            ctx=ctx,
            success=True
        )
    
    # 결과가 있는 경우
    result_embed = create_embed(
        title="🔍 차단 로그 검색 결과",
        description=f"**`{player}`**님의 차단 로그 **{len(ban_logs)}건**을 찾았습니다.",
        color=0x3498DB,
        ctx=ctx,
        success=True
    )
    
    # 최대 표시 개수만큼 로그 추가
    display_logs = ban_logs[:MAX_DISPLAY_LOGS]
    for i, log in enumerate(display_logs):
        log_date = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        result_embed.add_field(
            name=f"📋 로그 {i+1}",
            value=f"[메시지 링크]({log['jump_url']})\n"
                  f"📅 생성일: {log_date}\n"
                  f"👤 기록자: {log['author']}",
            inline=False
        )
    
    # 더 많은 로그가 있는 경우 안내
    if len(ban_logs) > MAX_DISPLAY_LOGS:
        result_embed.add_field(
            name="ℹ️ 추가 정보",
            value=f"총 **{len(ban_logs)}건** 중 최근 **{MAX_DISPLAY_LOGS}건**만 표시됩니다.\n"
                  f"더 자세한 검색은 차단 로그 채널에서 직접 검색해주세요.",
            inline=False
        )
    
    return result_embed


async def handle_searchbanlog_command(
    ctx: discord.ApplicationContext, 
    player: str
) -> None:
    """
    로그 검색 명령어 처리 로직
    
    Args:
        ctx: Discord 상호작용 객체
        player: 검색할 플레이어명
    """
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "searchbanlog", 
            {"player": player, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 처리 중 메시지 표시
    processing_embed = _create_processing_embed(ctx, player)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 로그 검색 실행
    ban_logs = await execute_searchbanlog_action(player, ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_search_result_embed(ctx, player, ban_logs)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    await command_logger.log_command_usage(
        ctx, 
        "searchbanlog", 
        {"player": player, "found_count": len(ban_logs)}, 
        success=True
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="로그검색", description="플레이어의 차단 로그를 검색합니다.")
    async def searchbanlog_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="검색할 플레이어 이름")
    ):
        """플레이어의 차단 로그 검색."""
        await handle_searchbanlog_command(ctx, player)