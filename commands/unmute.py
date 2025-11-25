"""채팅 뮤트 해제 명령어."""
import asyncio
import logging

import discord

from core.command_bridge import send_ilunar_command
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import COMMAND_DELAY

logger = logging.getLogger(__name__)


async def execute_unmute_action(player: str, bot, ctx: discord.ApplicationContext) -> bool:
    """뮤트 해제 실행."""
    try:
        unmute_command = f"cmi unmute {player}"
        
        if not await send_ilunar_command(bot, unmute_command, ctx):
            logger.error(f"Failed to send unmute command for player: {player}")
            return False
        
        await asyncio.sleep(COMMAND_DELAY)
        return True
        
    except Exception as e:
        logger.exception(f"Error executing unmute action for player {player}: {e}")
        return False


async def handle_unmute_command(ctx: discord.ApplicationContext, player: str) -> None:
    """뮤트 해제 명령어 처리."""
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "unmute", {"player": player, "error": "권한 부족"}, success=False
        )
        return
    
    processing_embed = create_embed(
        title="⏳ 처리 중...",
        description=f"**`{player}`**님의 뮤트 해제를 처리하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success = await execute_unmute_action(player, ctx.bot, ctx)
    
    await command_logger.log_command_usage(ctx, "unmute", {"player": player}, success=success)
    
    result_embed = _create_result_embed(player, success, ctx)
    await ctx.edit(embed=result_embed)


def _create_result_embed(player: str, success: bool, ctx: discord.ApplicationContext) -> discord.Embed:
    if success:
        embed = create_embed(
            title="🔊 뮤트 해제 완료",
            description=f"**`{player}`**님이 성공적으로 뮤트 해제되었습니다.",
            color=0x00FF00,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 뮤트 해제 실패",
            description=f"**`{player}`**님의 뮤트 해제 처리 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot) -> None:
    @bot.slash_command(name="unmute", description="플레이어의 뮤트를 해제합니다.")
    async def unmute_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="뮤트 해제할 플레이어 이름")
    ) -> None:
        await handle_unmute_command(ctx, player)