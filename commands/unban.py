import asyncio
import logging

import discord

from core.command_bridge import send_proxy_command
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import COMMAND_DELAY

logger = logging.getLogger(__name__)


async def execute_unban_action(player: str, bot, ctx: discord.ApplicationContext) -> bool:
    try:
        if not await send_proxy_command(bot, f"unban {player}", ctx):
            return False
        
        await asyncio.sleep(COMMAND_DELAY)
        return True
        
    except Exception as e:
        logger.error(f"차단 해제 실행 오류: {e}")
        return False


async def handle_unban_command(ctx: discord.ApplicationContext, player: str) -> None:
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "unban", {"player": player, "error": "권한 부족"}, success=False
        )
        return
    
    processing_embed = create_embed(
        title="⏳ 처리 중...",
        description=f"**`{player}`**님의 차단 해제를 처리하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success = await execute_unban_action(player, ctx.bot, ctx)
    
    await command_logger.log_command_usage(ctx, "unban", {"player": player}, success=success)
    
    result_embed = _create_result_embed(player, success, ctx)
    await ctx.edit(embed=result_embed)


def _create_result_embed(player: str, success: bool, ctx: discord.ApplicationContext) -> discord.Embed:
    if success:
        embed = create_embed(
            title="✅ 차단 해제 완료",
            description=f"**`{player}`**님이 성공적으로 차단 해제되었습니다.",
            color=0x00FF00,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 차단 해제 실패",
            description=f"**`{player}`**님의 차단 해제 처리 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot) -> None:
    @bot.slash_command(name="unban", description="플레이어의 차단을 해제합니다.")
    async def unban_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="차단 해제할 플레이어 이름")
    ) -> None:
        await handle_unban_command(ctx, player)