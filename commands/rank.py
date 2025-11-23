import asyncio
import logging
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import PROCESSING_DELAY

logger = logging.getLogger(__name__)

RANKS = {
    "default": "default",
    "lite": "lite",
    "special": "special",
    "premium": "premium",
    "ultra": "ultra",
    "booster": "booster",
    "youtuber": "youtuber",
    # "mod": "mod",
    # "admin": "admin",
    # "owner": "owner"
}


async def execute_rank_action(
    player: str, 
    rank: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> bool:
    from core.command_bridge import send_ilunar_command
    
    try:
        # V1 방식: LuckPerms 명령어로 등급 변경
        rank_command = f"lp user {player} parent set {rank}"
        
        logger.debug(f"Rank command: \'{rank_command}\'")
        
        rank_success = await send_ilunar_command(bot, rank_command, ctx)
        
        if not rank_success:
            return False
            
        await asyncio.sleep(PROCESSING_DELAY)
        return True
        
    except Exception as e:
        logger.error(f"등급 변경 실행 오류: {e}")
        return False


def _validate_rank(rank: str) -> bool:
    return rank in RANKS


def _create_invalid_rank_embed(ctx: discord.ApplicationContext, rank: str) -> discord.Embed:
    available_ranks_text = ", ".join(f"`{r}`" for r in RANKS.keys())
    
    return create_embed(
        title="❌ 유효하지 않은 등급",
        description=f"**{rank}**은(는) 유효하지 않은 등급입니다.\n\n**사용 가능한 등급**:\n{available_ranks_text}",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_processing_embed(ctx: discord.ApplicationContext, player: str, rank: str) -> discord.Embed:
    return create_embed(
        title="⏳ 처리 중...",
        description=f"**`{player}`**님의 등급을 **{rank}**(으)로 변경하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_result_embed(
    ctx: discord.ApplicationContext,
    player: str,
    rank: str,
    success: bool
) -> discord.Embed:
    if success:
        embed = create_embed(
            title="🏆 등급 변경 완료",
            description=f"**`{player}`**님의 등급이 성공적으로 **{rank}**(으)로 변경되었습니다.",
            color=0x00FF00,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 등급 변경 실패",
            description=f"**`{player}`**님의 등급 변경 처리 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="🏆 설정 등급", value=f"`{rank}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


async def handle_rank_command(ctx: discord.ApplicationContext, player: str, rank: str) -> None:
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "rank", 
            {"player": player, "rank": rank, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 등급 유효성 검증 (choices로 제한되므로 실제로는 불필요하지만 안전성을 위해 유지)
    if not _validate_rank(rank):
        await command_logger.log_command_usage(
            ctx,
            "rank",
            {"player": player, "rank": rank, "error": "유효하지 않은 등급"},
            success=False
        )
        
        invalid_rank_embed = _create_invalid_rank_embed(ctx, rank)
        await ctx.respond(embed=invalid_rank_embed, ephemeral=True)
        return
    
    # 처리 중 메시지
    processing_embed = _create_processing_embed(ctx, player, rank)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 등급 변경 실행
    success = await execute_rank_action(player, rank, ctx.bot, ctx)
    
    # 결과 전송
    result_embed = _create_result_embed(ctx, player, rank, success)
    await ctx.edit(embed=result_embed)
    
    # 로깅
    await command_logger.log_command_usage(
        ctx, 
        "rank", 
        {"player": player, "rank": rank}, 
        success=success
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="rank", description="플레이어의 등급을 변경합니다.")
    async def rank_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="등급을 변경할 플레이어 이름"),
        rank: str = discord.Option(str, description="변경할 등급")
    ):
        """플레이어의 등급 변경."""
        await handle_rank_command(ctx, player, rank)