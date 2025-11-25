"""추천 보상 지급 명령어."""
import asyncio
import logging
from typing import Dict, Any, Optional
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import PROCESSING_DELAY

logger = logging.getLogger(__name__)


async def execute_vote_action(player: str, bot, ctx: discord.ApplicationContext) -> bool:
    """추천 보상 지급 실행."""
    from core.command_bridge import send_console_command, send_proxy_command
    
    try:
        # 추천 보상 지급 명령어 전송
        vote_command = f"getvote {player}"
        vote_success = await send_console_command(
            bot, vote_command, ctx.user.mention
        )
        
        if not vote_success:
            return False
            
        await asyncio.sleep(PROCESSING_DELAY)
        return True
        
    except Exception as e:
        logger.error(f"추천 보상 지급 실행 오류: {e}")
        return False


def _validate_player_name(player: str) -> Dict[str, Any]:
    """플레이어명 유효성 검증."""
    if len(player) < 3 or len(player) > 16:
        return {
            "valid": False,
            "error": "플레이어명은 3~16글자 사이여야 합니다."
        }
    
    # 기본 문자 검증
    if not player.replace("_", "").isalnum():
        return {
            "valid": False,
            "error": "플레이어명은 영문, 숫자, 언더스코어(_)만 사용할 수 있습니다."
        }
    
    return {"valid": True, "error": None}


def _create_permission_error_embed(ctx: discord.ApplicationContext) -> discord.Embed:
    return create_embed(
        title="❌ 권한 부족",
        description="이 명령어를 사용할 권한이 없습니다.\n**필요 권한**: `스탭`",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_validation_error_embed(ctx: discord.ApplicationContext, error: str) -> discord.Embed:
    return create_embed(
        title="❌ 유효하지 않은 플레이어명",
        description=f"플레이어명이 유효하지 않습니다.\n\n**오류**: {error}",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_processing_embed(ctx: discord.ApplicationContext, player: str) -> discord.Embed:
    return create_embed(
        title="🎁 추천 보상 지급 중...",
        description=f"**`{player}`**님에게 추천 보상을 지급하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_result_embed(
    ctx: discord.ApplicationContext,
    player: str,
    success: bool
) -> discord.Embed:
    if success:
        embed = create_embed(
            title="🎁 추천 보상 지급 완료",
            description=f"**`{player}`**님에게 추천 보상이 성공적으로 지급되었습니다.",
            color=0x00FF00,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 추천 보상 지급 실패",
            description=f"**`{player}`**님의 추천 보상 지급 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    # 상세 정보 필드 추가
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


async def handle_vote_command(ctx: discord.ApplicationContext, player: str) -> None:
    """추천 보상 지급 명령어 처리."""
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "vote", 
            {"player": player, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 플레이어명 유효성 검증
    validation_result = _validate_player_name(player)
    if not validation_result["valid"]:
        await command_logger.log_command_usage(
            ctx,
            "vote",
            {"player": player, "error": validation_result["error"]},
            success=False
        )
        
        validation_error_embed = _create_validation_error_embed(
            ctx, validation_result["error"]
        )
        await ctx.respond(embed=validation_error_embed, ephemeral=True)
        return
    
    # 처리 중 메시지 표시
    processing_embed = _create_processing_embed(ctx, player)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 추천 보상 지급 실행
    success = await execute_vote_action(player, ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_result_embed(ctx, player, success)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    await command_logger.log_command_usage(
        ctx, 
        "vote", 
        {"player": player}, 
        success=success
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="vote", description="플레이어에게 추천 보상을 지급합니다.")
    async def vote_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="추천 보상을 받을 플레이어 이름")
    ):
        """플레이어에게 추천 보상 지급."""
        await handle_vote_command(ctx, player)