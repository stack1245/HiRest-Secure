"""도움말 명령어."""
from typing import Dict, List

import discord
from discord.ext import commands

from utils.utils import CommandLogger, create_embed

BOT_NAME = "HiRest Bot"
BOT_VERSION = "v2.0"
BOT_COLOR = 0x0099FF

GITHUB_URL = "https://github.com/stack1245/hrbot-v2"
DISCORD_URL = "https://discord.gg/hrst"

COMMAND_GROUPS: Dict[str, List[str]] = {
    "👤 플레이어 관리": [
        "`/ban <player> [reason]` - 영구 차단 및 로그 업로드",
        "`/tempban <player> <time> [reason]` - 임시 차단",
        "`/unban <player>` - 차단 해제",
        "`/kick <player> [reason]` - 서버에서 추방",
        "`/mute <player> <time> [reason]` - 채팅 금지",
        "`/unmute <player>` - 뮤트 해제"
    ],
    "ℹ️ 정보 조회": [
        "`/list` - 온라인 플레이어 등급별 조회",
        "`/info <player>` - 플레이어 상세 정보 조회"
    ],
    "🎮 플레이어 설정": [
        "`/rank <player> <rank>` - 플레이어 권한 설정",
        "`/nick <player> <code>` - 닉네임 변경",
        "`/vote <player>` - 추천 보상 지급",
        "`/checkvote <vote_id> [server_id]` - 추천 정보 조회"
    ],
    "📝 로그 관리": [
        "`/로그검색 <player>` - 차단 로그 검색",
        "`/로그업로드 <player> [reason]` - 차단 없이 로그만 업로드",
        "`/중복제거 [player]` - 중복 차단 로그 제거",
        "`/로그삭제 <player>` - 플레이어 차단 로그 완전 삭제"
    ],
    "⚙️ 시스템": [
        "`/command` - 직접 명령어 입력"
    ]
}

USAGE_GUIDE: List[str] = [
    "• `<>`: 필수 매개변수",
    "• `[]`: 선택적 매개변수",
    "• 모든 명령어는 스탭 권한이 필요합니다",
    "• 시간 형식: `1d` (일), `1h` (시간), `1m` (분), `1s` (초)"
]


def create_help_embed(ctx: discord.ApplicationContext) -> discord.Embed:
    embed = create_embed(
        title=f"🤖 {BOT_NAME} 도움말 {BOT_VERSION}",
        description=(
            "**HiRest 마인크래프트 서버 종합 관리 봇입니다.**\n"
            "모든 명령어는 `/`로 시작하며 스탭 역할이 필요합니다."
        ),
        color=BOT_COLOR,
        ctx=ctx
    )
    
    for group_name, commands_list in COMMAND_GROUPS.items():
        commands_text = "\n".join(commands_list)
        embed.add_field(
            name=group_name,
            value=commands_text,
            inline=False
        )
    
    usage_text = "\n".join(USAGE_GUIDE)
    embed.add_field(
        name="📋 사용법",
        value=usage_text,
        inline=False
    )
    
    embed.add_field(
        name="🔗 링크 및 정보",
        value=(
            f"[GitHub]({GITHUB_URL}) | [Discord 서버]({DISCORD_URL})\n"
            f"**버전**: {BOT_VERSION} | **제작**: Team. HiRest"
        ),
        inline=False
    )
    
    total_commands = sum(len(cmd_list) for cmd_list in COMMAND_GROUPS.values())
    embed.add_field(
        name="📊 통계",
        value=f"총 **{total_commands}개**의 명령어 사용 가능",
        inline=False
    )

    return embed


async def handle_help_command(ctx: discord.ApplicationContext) -> None:
    logger = CommandLogger()
    
    try:
        embed = create_help_embed(ctx)
        await ctx.respond(embed=embed, ephemeral=False)
        await logger.log_command_usage(ctx, "help", {}, success=True)
        
    except Exception as e:
        await logger.log_command_usage(
            ctx, 
            "help", 
            {"error": str(e)}, 
            success=False
        )
        
        error_embed = create_embed(
            title="❌ 오류 발생",
            description=f"도움말을 불러오는 중 오류가 발생했습니다.\n\n**오류**: {e}",
            color=0xE74C3C,
            ctx=ctx
        )
        
        if ctx.response.is_done():
            await ctx.edit(embed=error_embed)
        else:
            await ctx.respond(embed=error_embed, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    """명령어 등록."""
    
    @bot.slash_command(name="help", description="봇의 명령어 목록을 보여줍니다.")
    async def help_command(ctx: discord.ApplicationContext) -> None:
        """봇의 명령어 목록을 보여줍니다."""
        await handle_help_command(ctx)