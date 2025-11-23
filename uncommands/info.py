import asyncio
import logging
import re
from typing import Dict, Optional

import discord

from core.command_bridge import send_console_command
from core.config import get_config
from utils.utils import (
    create_embed, 
    CommandLogger, 
    ConsoleResponseHandler,
    parse_player_info
)
from utils.decorators import check_staff_permission
from utils.constants import CONSOLE_RESPONSE_DELAY

logger = logging.getLogger(__name__)


async def execute_info_action(
    player: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> Dict[str, str]:
    config = get_config()
    
    try:
        if not await send_console_command(
            bot, f"cmi info {player}", ctx.user.mention, silent=True
        ):
            return {"error": "콘솔 명령어 전송 실패"}
        
        response_handler = ConsoleResponseHandler(
            bot, config.ILUNAR_CONSOLE_CHANNEL_ID
        )
        console_response = await response_handler.wait_for_response(
            ctx.user.mention, 
            timeout=CONSOLE_RESPONSE_DELAY + 2.0,
            keywords=["Display name:", player]
        )
        
        if console_response:
            player_info = parse_player_info(console_response, player)
            if player_info:
                return player_info
        
        return {
            "error": (
                f"플레이어 '{player}'의 정보를 찾을 수 없습니다.\n"
                f"닉네임을 정확히 입력했는지 확인해주세요."
            )
        }
        
    except Exception as e:
        logger.error(f"플레이어 정보 조회 오류: {e}")
        return {"error": str(e)}


async def handle_info_command(
    ctx: discord.ApplicationContext, 
    player: str
) -> None:
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "info", 
            {"player": player, "error": "권한 부족"}, 
            success=False
        )
        return
    
    processing_embed = create_embed(
        title="⏳ 정보 조회 중...",
        description=f"**`{player}`**님의 정보를 조회하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    info_data = await execute_info_action(player, ctx.bot, ctx)
    success = "error" not in info_data
    
    await command_logger.log_command_usage(
        ctx, 
        "info", 
        {"player": player, "success": success}, 
        success=success
    )
    
    result_embed = _create_result_embed(
        info_data, player, ctx, success
    )
    await ctx.edit(embed=result_embed)


def _create_result_embed(
    info_data: Dict[str, str], 
    player: str, 
    ctx: discord.ApplicationContext, 
    success: bool
) -> discord.Embed:
    if not success:
        return create_embed(
            title="정보 조회 실패",
            description=(
                f"**`{player}`**님의 정보 조회 중 오류가 발생했습니다.\n\n"
                f"**오류**: {info_data['error']}"
            ),
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    username = info_data['username']
    display_name = info_data.get('display_name')
    
    player_name = (
        f"`{username}` ({display_name})" 
        if display_name 
        else f"`{username}`"
    )
    
    embed = create_embed(
        title="ℹ️ 플레이어 정보",
        description="",
        color=0x3498DB,
        ctx=ctx,
        success=True
    )
    
    embed.add_field(name="🎮 닉네임", value=player_name, inline=False)
    
    if info_data.get('uuid'):
        embed.add_field(
            name="🆔 UUID", 
            value=f"`{info_data['uuid']}`", 
            inline=False
        )
    
    if info_data.get('ip'):
        embed.add_field(
            name="🌐 IP 주소", 
            value=f"`{info_data['ip']}`", 
            inline=False
        )
    
    status = info_data.get('status', '알 수 없음')
    status_emoji = {"온라인": "🟢", "오프라인": "🔴"}.get(status, "⚪")
    embed.add_field(
        name="📊 온라인 상태", 
        value=f"{status_emoji} `{status}`", 
        inline=False
    )
    
    return embed


def setup(bot) -> None:
    """명령어 등록."""
    
    @bot.slash_command(name="info", description="플레이어의 정보를 조회합니다.")
        async def info_func(
        ctx: discord.ApplicationContext, 
        player: str
    ) -> None:
        await handle_info_command(ctx, player)