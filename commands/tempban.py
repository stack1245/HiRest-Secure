import asyncio
import logging
from typing import Optional

import discord

from core.command_bridge import send_proxy_command
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import (
    tempban_duration_autocomplete,
    tempban_reason_autocomplete,
    COMMAND_DELAY
)

logger = logging.getLogger(__name__)

DEFAULT_REASON = "사유 없음"


async def execute_tempban_action(player: str, duration: str, reason: str, bot, ctx: discord.ApplicationContext) -> bool:
    try:
        tempban_command = f"tempban {player} {duration} {reason}"
        logger.debug(f"Tempban command: '{tempban_command}'")
        
        if not await send_proxy_command(bot, tempban_command, ctx):
            logger.error(f"Failed to send tempban command for player: {player}")
            return False
        
        await asyncio.sleep(COMMAND_DELAY)
        return True
        
    except Exception as e:
        logger.exception(f"Error executing tempban action for player {player}: {e}")
        return False


async def handle_tempban_command(ctx: discord.ApplicationContext, player: str, duration: str = "1h", reason: str = DEFAULT_REASON) -> None:
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "tempban", {"player": player, "duration": duration, "reason": reason, "error": "권한 부족"}, success=False
        )
        return
    
    processing_embed = create_embed(
        title="처리 중...",
        description=f"**`{player}`**님의 임시 차단을 처리하고 있습니다...",
        color=0xF39C12
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success = await execute_tempban_action(player, duration, reason, ctx.bot, ctx)
    
    await command_logger.log_command_usage(
        ctx, "tempban", {"player": player, "duration": duration, "reason": reason}, success=success
    )
    
    result_embed = _create_result_embed(player, duration, reason, success, ctx)
    await ctx.edit(embed=result_embed)


def _create_result_embed(player: str, duration: str, reason: str, success: bool, ctx: discord.ApplicationContext) -> discord.Embed:
    if success:
        embed = create_embed(
            title="임시 차단 완료",
            description=f"**`{player}`**님이 성공적으로 임시 차단되었습니다.",
            success=True
        )
    else:
        embed = create_embed(
            title="임시 차단 실패",
            description=f"**`{player}`**님의 임시 차단 처리 중 오류가 발생했습니다.",
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="⏰ 기간", value=f"`{duration}`", inline=False)
    embed.add_field(name="📝 사유", value=f"`{reason}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot) -> None:
    @bot.slash_command(name="tempban", description="플레이어를 임시 차단합니다.")
    async def tempban_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="임시 차단할 플레이어 이름"),
        duration: str = discord.Option(str, description="차단 기간 (예: 1h, 1d, 30m)", autocomplete=tempban_duration_autocomplete),
        reason: str = discord.Option(str, description="차단 사유", default=DEFAULT_REASON, autocomplete=tempban_reason_autocomplete)
    ) -> None:
        """플레이어 임시 차단."""
        await handle_tempban_command(ctx, player, duration, reason)