import asyncio
import logging
import re
from typing import Dict, Any, Optional
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission
from utils.constants import PROCESSING_DELAY

logger = logging.getLogger(__name__)

MAX_NICKNAME_LENGTH = 16
MIN_NICKNAME_LENGTH = 3

VALID_NICKNAME_PATTERN = re.compile(r'^[a-zA-Z0-9가-힣_]{3,16}$')
FORBIDDEN_PATTERNS = [
    r'admin', r'owner', r'mod', r'staff', r'console', 
    r'server', r'hirest', r'bot'
]


async def execute_nick_action(
    player: str, 
    code: str, 
    bot, 
    ctx: discord.ApplicationContext
) -> bool:
    from core.command_bridge import send_ilunar_command
    
    try:
        # 사양서 기준: .s ilunar cmi nick <code> <player>
        nick_command = f"cmi nick {code} {player}"
        
        logger.debug(f"Nick command: \'{nick_command}\'")
        
        nick_success = await send_ilunar_command(bot, nick_command, ctx)
        
        if not nick_success:
            return False
            
        await asyncio.sleep(PROCESSING_DELAY)
        return True
        
    except Exception as e:
        logger.error(f"닉네임 변경 실행 오류: {e}")
        return False


def _validate_nickname(code: str) -> Dict[str, Any]:
    # 띄어쓰기 검증 (사양서 제약사항)
    if ' ' in code:
        return {
            "valid": False,
            "error": "닉네임 코드에 띄어쓰기를 사용할 수 없습니다."
        }
    
    # 길이 검증
    if len(code) < MIN_NICKNAME_LENGTH:
        return {
            "valid": False,
            "error": f"닉네임 코드는 최소 {MIN_NICKNAME_LENGTH}글자 이상이어야 합니다."
        }
    
    if len(code) > MAX_NICKNAME_LENGTH:
        return {
            "valid": False,
            "error": f"닉네임 코드는 최대 {MAX_NICKNAME_LENGTH}글자 이하여야 합니다."
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
        title="❌ 유효하지 않은 닉네임 코드",
        description=f"닉네임 코드가 유효하지 않습니다.\n\n**오류**: {error}\n\n"
                   f"**규칙**:\n"
                   f"• 길이: {MIN_NICKNAME_LENGTH}~{MAX_NICKNAME_LENGTH}글자\n"
                   f"• 띄어쓰기 사용 불가",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_processing_embed(
    ctx: discord.ApplicationContext, 
    player: str, 
    code: str
) -> discord.Embed:
    return create_embed(
        title="⏳ 처리 중...",
        description=f"**`{player}`**님의 닉네임을 **{code}**(으)로 변경하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_result_embed(
    ctx: discord.ApplicationContext,
    player: str,
    code: str,
    success: bool
) -> discord.Embed:
    if success:
        embed = create_embed(
            title="🏷️ 닉네임 변경 완료",
            description=f"**`{player}`**님의 닉네임이 성공적으로 변경되었습니다.",
            color=0x3498DB,
            ctx=ctx,
            success=True
        )
    else:
        embed = create_embed(
            title="❌ 닉네임 변경 실패",
            description=f"**`{player}`**님의 닉네임 변경 처리 중 오류가 발생했습니다.",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    
    # 상세 정보 필드 추가
    embed.add_field(name="🎮 플레이어", value=f"`{player}`", inline=False)
    embed.add_field(name="🏷️ 닉네임 코드", value=f"`{code}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


async def handle_nick_command(
    ctx: discord.ApplicationContext, 
    player: str, 
    code: str
) -> None:
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "nick", 
            {"player": player, "code": code, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 닉네임 코드 유효성 검증
    validation_result = _validate_nickname(code)
    if not validation_result["valid"]:
        await command_logger.log_command_usage(
            ctx,
            "nick",
            {"player": player, "code": code, "error": validation_result["error"]},
            success=False
        )
        
        validation_error_embed = _create_validation_error_embed(
            ctx, validation_result["error"]
        )
        await ctx.respond(embed=validation_error_embed, ephemeral=True)
        return
    
    # 처리 중 메시지 표시
    processing_embed = _create_processing_embed(ctx, player, code)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 닉네임 변경 실행
    success = await execute_nick_action(player, code, ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_result_embed(ctx, player, code, success)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    await command_logger.log_command_usage(
        ctx, 
        "nick", 
        {"player": player, "code": code}, 
        success=success
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="nick", description="플레이어의 닉네임을 변경합니다.")
    @app_commands.describe(
        player="닉네임을 변경할 플레이어 이름",
        code="새로 설정할 닉네임 코드 (띄어쓰기 불가)"
    )
    async def nick_func(ctx: discord.ApplicationContext, player: str, code: str):
        """플레이어의 닉네임 변경."""
        await handle_nick_command(ctx, player, code)