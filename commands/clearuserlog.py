import asyncio
import logging
from typing import Dict, Any, Optional
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 2000
DELETE_DELAY = 0.5

BAN_LOG_PATTERN = "## <:hr_ban:1350451179683057764> 차단 로그"


async def execute_clearuserlog_action(
    player: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> int:
    from core.config import get_config
    
    config = get_config()
    
    try:
        # 길드 및 채널 확인
        guild = bot.get_guild(config.TARGET_GUILD_ID)
        if not guild:
            logger.error(f"길드를 찾을 수 없습니다: {config.TARGET_GUILD_ID}")
            return 0
        
        ban_log_channel = guild.get_channel(config.BAN_LOG_CHANNEL_ID)
        if not ban_log_channel:
            logger.error(f"차단 로그 채널을 찾을 수 없습니다: {config.BAN_LOG_CHANNEL_ID}")
            return 0
        
        deleted_count = 0
        
        # 대상 메시지 수집
        target_messages = []
        async for message in ban_log_channel.history(limit=MAX_SEARCH_LIMIT):
            if _is_target_ban_log(message, player):
                target_messages.append(message)
        
        # 메시지 삭제 (역순으로 삭제하여 안정성 확보)
        for message in reversed(target_messages):
            try:
                await message.delete()
                deleted_count += 1
                await asyncio.sleep(DELETE_DELAY)
            except discord.NotFound:
                continue
            except Exception as e:
                logger.error(f"메시지 삭제 실패 (ID: {message.id}): {e}")
                continue
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"로그 삭제 중 오류 발생: {e}")
        return 0


def _is_target_ban_log(message: discord.Message, player: str) -> bool:
    if not message.content:
        return False
        
    # 차단 로그 패턴 확인
    if BAN_LOG_PATTERN not in message.content:
        return False
    
    # 플레이어명 확인 (백틱으로 감싸진 형태)
    return f"`{player}`" in message.content


async def handle_clearuserlog_command(
    ctx: discord.ApplicationContext, 
    player: str
) -> None:
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "clearuserlog", 
            {"player": player, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 처리 중 메시지 표시
    processing_embed = create_embed(
        title="🗑️ 로그 삭제 중...",
        description=f"**`{player}`**님의 차단 로그를 삭제하고 있습니다...\n"
                   f"⚠️ 이 작업은 되돌릴 수 없습니다.",
        color=0xF39C12,
        ctx=ctx
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 로그 삭제 실행
    deleted_count = await execute_clearuserlog_action(player, ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_deletion_result_embed(ctx, player, deleted_count)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    await command_logger.log_command_usage(
        ctx, 
        "clearuserlog", 
        {"player": player, "deleted_count": deleted_count}, 
        success=True
    )


def _create_deletion_result_embed(
    ctx: discord.ApplicationContext,
    player: str,
    deleted_count: int
) -> discord.Embed:
    if deleted_count > 0:
        embed = create_embed(
            title="🗑️ 로그 삭제 완료",
            description=f"**`{player}`**님의 차단 로그 **{deleted_count}건**을 성공적으로 삭제했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=True
        )
        
        embed.add_field(
            name="⚠️ 주의사항",
            value="삭제된 로그는 복구할 수 없습니다.\n필요시 백업을 확인해주세요.",
            inline=False
        )
    else:
        embed = create_embed(
            title="🗑️ 로그 삭제 결과",
            description=f"**`{player}`**님의 차단 로그를 찾을 수 없습니다.\n"
                       f"이미 삭제되었거나 존재하지 않는 플레이어일 수 있습니다.",
            color=0x95A5A6,
            ctx=ctx,
            success=True
        )
    
    embed.add_field(name="🎮 대상 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="로그삭제", description="플레이어의 차단 로그를 삭제합니다.")
    async def clearuserlog_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="로그를 삭제할 플레이어 이름")
    ):
        """플레이어의 차단 로그 삭제."""
        await handle_clearuserlog_command(ctx, player)