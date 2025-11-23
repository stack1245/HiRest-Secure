import asyncio
import logging
import re
from typing import Tuple

import discord

from core.command_bridge import send_ilunar_command
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import (
    mute_duration_autocomplete,
    mute_reason_autocomplete,
    COMMAND_DELAY
)

logger = logging.getLogger(__name__)

DEFAULT_REASON = "규칙 위반"

TIME_MULTIPLIERS = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    '': 60
}

TIME_UNIT_NAMES = {
    's': '초',
    'm': '분',
    'h': '시간',
    'd': '일',
    '': '분'
}

PERMANENT_KEYWORDS = ["permanent", "perm", "영구", "영원"]


def parse_duration(duration_str: str) -> Tuple[int, str]:
    if duration_str.lower() in PERMANENT_KEYWORDS:
        return 0, "영구"
    
    match = re.match(r'^(\d+)\s*([smhd]?)$', duration_str.lower())
    if not match:
        return -1, "잘못된 형식"
    
    value, unit = match.groups()
    value = int(value)
    
    total_seconds = value * TIME_MULTIPLIERS.get(unit, 60)
    friendly = f"{value}{TIME_UNIT_NAMES.get(unit, '분')}"
    
    return total_seconds, friendly


def _convert_seconds_to_time_format(duration_seconds: int) -> str:
    if duration_seconds >= 86400:  # 일 단위
        return f"{duration_seconds // 86400}d"
    elif duration_seconds >= 3600:  # 시간 단위
        return f"{duration_seconds // 3600}h"
    elif duration_seconds >= 60:  # 분 단위
        return f"{duration_seconds // 60}m"
    else:  # 초 단위
        return f"{duration_seconds}s"


async def execute_mute_action(player: str, duration_seconds: int, reason: str, bot, ctx: discord.ApplicationContext) -> bool:
    try:
        time_str = _convert_seconds_to_time_format(duration_seconds)
        mute_command = f"cmi mute {player} {time_str} {reason}"
        
        logger.debug(f"Mute command: '{mute_command}'")
        
        if not await send_ilunar_command(bot, mute_command, ctx):
            logger.error(f"Failed to send mute command for player: {player}")
            return False
        
        await asyncio.sleep(COMMAND_DELAY)
        return True
        
    except Exception as e:
        logger.exception(f"Error executing mute action for player {player}: {e}")
        return False


async def handle_mute_command(ctx: discord.ApplicationContext, player: str, duration: str = "permanent", reason: str = DEFAULT_REASON) -> None:
    command_logger = CommandLogger()
    
    # 권한 확인
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "mute", {"player": player, "duration": duration, "reason": reason, "error": "권한 부족"}, success=False
        )
        return
    
    # 기간 파싱
    seconds, friendly_duration = parse_duration(duration)
    
    if seconds == -1:
        embed = create_embed(
            title="❌ 잘못된 기간 형식",
            description="기간 형식이 올바르지 않습니다.\n\n**사용 가능한 형식:**\n• `30s` - 30초\n• `5m` - 5분\n• `1h` - 1시간\n• `1d` - 1일\n• `permanent` - 영구",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    
    processing_embed = create_embed(
        title="처리 중...",
        description=f"**`{player}`**님의 뮤트를 처리하고 있습니다...",
        color=0xF39C12
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success = await execute_mute_action(player, seconds, reason, ctx.bot, ctx)
    
    await command_logger.log_command_usage(
        ctx, "mute", {"player": player, "duration": duration, "reason": reason}, success=success
    )
    
    result_embed = _create_result_embed(player, friendly_duration, reason, seconds, success, ctx)
    await ctx.edit(embed=result_embed)


def _create_result_embed(player: str, friendly_duration: str, reason: str, seconds: int, success: bool, ctx: discord.ApplicationContext) -> discord.Embed:
    if success:
        embed = create_embed(
            title="뮤트 완료",
            description=f"**`{player}`**님이 성공적으로 뮤트되었습니다.",
            success=True
        )
    else:
        embed = create_embed(
            title="뮤트 실패",
            description=f"**`{player}`**님의 뮤트 처리 중 오류가 발생했습니다.",
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="⏰ 기간", value=f"`{friendly_duration}`", inline=False)
    embed.add_field(name="📝 사유", value=f"`{reason}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    if success and seconds > 0:
        embed.add_field(
            name="🕐 해제 예정",
            value=f"<t:{int(ctx.created_at.timestamp() + seconds)}:R>",
            inline=False
        )
    
    return embed


def setup(bot) -> None:
    @bot.slash_command(name="mute", description="플레이어를 뮤트합니다.")
    async def mute_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="뮤트할 플레이어 이름"),
        duration: str = discord.Option(str, description="뮤트 기간 (예: 30s, 5m, 1h, 1d, permanent)", default="permanent", autocomplete=mute_duration_autocomplete),
        reason: str = discord.Option(str, description="뮤트 사유", default=DEFAULT_REASON, autocomplete=mute_reason_autocomplete)
    ) -> None:
        """플레이어 지정된 기간 동안 뮤트."""
        await handle_mute_command(ctx, player, duration, reason)