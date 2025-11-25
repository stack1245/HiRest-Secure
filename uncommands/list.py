"""온라인 플레이어 목록 명령어."""
import asyncio
import logging
from typing import Dict, Any, List
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import PROCESSING_DELAY

logger = logging.getLogger(__name__)

MAX_EMBED_TITLE_LENGTH = 256

RANK_DISPLAY_ORDER = [
    "special", "default", "premium", "lite", "ultra", 
    "booster", "youtuber", "mod", "admin", "owner"
]

RANK_EMOJIS = {
    "default": "😀", 
    "lite": "💎",
    "special": "💎",
    "premium": "💎",
    "ultra": "💎",
    "booster": "💎",
    "youtuber": "📺",
    "mod": "🛠️",
    "admin": "🛠️",
    "owner": "👑"
}


async def execute_list_action(bot, ctx: discord.ApplicationContext) -> Dict[str, Any]:
    """온라인 플레이어 목록 조회 실행."""
    from core.command_bridge import send_console_command
    from core.config import get_config
    from utils.utils import ConsoleResponseHandler
    
    try:
        config = get_config()
        
        # 콘솔 명령어 전송
        list_success = await send_console_command(
            bot, "list", ctx.user.mention
        )
        
        if not list_success:
            return {"error": "콘솔 명령어 전송 실패"}
        
        # 콘솔 응답 대기 및 파싱
        response_handler = ConsoleResponseHandler(bot, config.ILUNAR_CONSOLE_CHANNEL_ID)
        console_response = await response_handler.wait_for_response(
            ctx.user.mention, 
            timeout=PROCESSING_DELAY,
            keywords=["Players online"]
        )
        
        if console_response:
            player_data = response_handler.parser.parse_player_list(console_response)
            return player_data
        else:
            logger.warning("콘솔 응답 없음, 기본값 사용")
            return _get_fallback_player_data()
        
    except Exception as e:
        logger.error(f"플레이어 목록 조회 오류: {e}")
        return {"error": str(e)}


def _get_fallback_player_data() -> Dict[str, Any]:
    return {
        "total_players": 0,
        "max_players": 999,
        "message": "현재 온라인 플레이어 정보를 가져올 수 없습니다."
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


def _create_processing_embed(ctx: discord.ApplicationContext) -> discord.Embed:
    """
    처리 중 상태 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        
    Returns:
        discord.Embed: 처리 중 임베드
    """
    return create_embed(
        title="⏳ 목록 조회 중...",
        description="온라인 플레이어 목록을 조회하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_result_embed(ctx: discord.ApplicationContext, list_data: Dict[str, Any]) -> discord.Embed:
    """
    목록 조회 결과 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        list_data: 플레이어 목록 데이터
        
    Returns:
        discord.Embed: 결과 임베드
    """
    if "error" in list_data:
        return create_embed(
            title="❌ 목록 조회 실패",
            description=f"플레이어 목록 조회 중 오류가 발생했습니다.\n\n**오류**: {list_data['error']}",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    # 메시지가 있는 경우 (응답이 없거나 파싱 실패)
    if "message" in list_data:
        return create_embed(
            title="📋 온라인 플레이어 목록",
            description=list_data["message"],
            color=0x95A5A6,
            ctx=ctx,
            success=True
        )
    
    # 성공 임베드 생성
    total_players = list_data.get("total_players", 0)
    max_players = list_data.get("max_players", 999)
    
    result_embed = create_embed(
        title="📋 온라인 플레이어 목록",
        description=f"현재 **{total_players}/{max_players}명**이 온라인입니다.",
        color=0x00FF00,
        ctx=ctx,
        success=True
    )
    
    # 등급별 플레이어 표시
    _add_player_fields(result_embed, list_data)
    
    return result_embed


def _add_player_fields(embed: discord.Embed, list_data: Dict[str, Any]) -> None:
    """
    임베드에 등급별 플레이어 필드를 추가합니다.
    
    Args:
        embed: 임베드 객체
        list_data: 플레이어 목록 데이터
    """
    for rank in RANK_DISPLAY_ORDER:
        if rank in list_data and list_data[rank]:
            players_text = ", ".join([f"`{player}`" for player in list_data[rank]])
            
            embed.add_field(
                name=f"{rank} ({len(list_data[rank])}명)",
                value=players_text,
                inline=False
            )


async def handle_list_command(ctx: discord.ApplicationContext) -> None:
    """
    플레이어 목록 조회 명령어 처리 로직
    
    Args:
        ctx: Discord 상호작용 객체
    """
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "list", {"error": "권한 부족"}, success=False
        )
        return
    
    # 처리 중 메시지 표시
    processing_embed = _create_processing_embed(ctx)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 목록 조회 실행
    list_data = await execute_list_action(ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_result_embed(ctx, list_data)
    await ctx.edit(embed=result_embed)
    
    # 성공 로깅
    await command_logger.log_command_usage(
        ctx, "list", list_data, success="error" not in list_data
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="list", description="온라인 플레이어 목록을 조회합니다.")
    async def list_func(ctx: discord.ApplicationContext):
        """온라인 플레이어 목록 조회."""
        await handle_list_command(ctx)