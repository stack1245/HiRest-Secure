"""킥 명령어."""
import asyncio
import logging

import discord

from core.command_bridge import send_ilunar_command
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import kick_reason_autocomplete, COMMAND_DELAY

DEFAULT_REASON = "사유 없음"

logger = logging.getLogger(__name__)


async def execute_kick_action(
    player: str, 
    reason: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> bool:
    """킥 실행."""
    try:
        kick_command = f"kick {player} {reason}"
        
        if not await send_ilunar_command(bot, kick_command, ctx):
            logger.error(f"킥 명령 전송 실패: {player}")
            return False
        
        await asyncio.sleep(COMMAND_DELAY)
        return True
        
    except Exception as e:
        logger.error(f"킥 실행 오류 ({player}): {e}")
        return False


async def handle_kick_command(
    ctx: discord.ApplicationContext, 
    player: str, 
    reason: str = DEFAULT_REASON
) -> None:
    """킥 명령어 처리."""
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "kick", 
            {"player": player, "reason": reason, "error": "권한 부족"}, 
            success=False
        )
        return
    
    processing_embed = create_embed(
        title="처리 중...",
        description=f"**`{player}`**님의 킥을 처리하고 있습니다...",
        color=0xF39C12
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success = await execute_kick_action(
        player, reason, ctx.bot, ctx
    )
    
    await command_logger.log_command_usage(
        ctx, "kick", {"player": player, "reason": reason}, success=success
    )
    
    result_embed = _create_result_embed(player, reason, success, ctx)
    await ctx.edit(embed=result_embed)


def _create_result_embed(
    player: str, 
    reason: str, 
    success: bool, 
    ctx: discord.ApplicationContext
) -> discord.Embed:
    """결과 임베드 생성."""
    if success:
        embed = create_embed(
            title="👢 킥 완료",
            description=f"**`{player}`**님이 성공적으로 킥되었습니다.",
            color=0xFF9500,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 킥 실패",
            description=f"**`{player}`**님의 킥 처리 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="📝 사유", value=f"`{reason}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot) -> None:
    """명령어 등록."""
    
    @bot.slash_command(name="kick", description="플레이어를 킥합니다.")
        # autocomplete: reason=kick_reason_autocomplete
    async def kick_func(
        ctx: discord.ApplicationContext, 
        player: str, 
        reason: str = DEFAULT_REASON
    ) -> None:
        await handle_kick_command(ctx, player, reason)