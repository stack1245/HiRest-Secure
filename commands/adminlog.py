import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord import option

from utils.decorators import check_staff_permission
from utils.utils import create_embed

logger = logging.getLogger(__name__)

# 채널 ID 상수
ENCHANT_LOG_CHANNEL_ID = 1434553344231473272
ROLLBACK_LOG_CHANNEL_ID = 1434553388820992100


def setup(bot: discord.Bot) -> None:
    """AdminLog 명령어 등록"""
    
    @bot.slash_command(
        name="관리기록",
        description="인첸트 지급 또는 복구 기록을 채널에 기록합니다"
    )
    @option(
        "유형",
        description="기록 유형을 선택하세요",
        choices=["인첸트", "복구기록"],
        required=True
    )
    @option(
        "닉네임",
        description="플레이어 닉네임",
        required=True
    )
    @option(
        "티켓번호",
        description="티켓 번호 (예: 1220)",
        required=True
    )
    @option(
        "내용",
        description="인첸트 내용 또는 복구 좌표",
        required=True
    )
    async def adminlog(
        ctx: discord.ApplicationContext,
        유형: str,
        닉네임: str,
        티켓번호: int,
        내용: str
    ):
        """관리 기록 명령어"""
        # 권한 확인
        if not await check_staff_permission(ctx):
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            # 현재 시간 포맷 (한국 시간 KST)
            kst = timezone(timedelta(hours=9))
            now = datetime.now(kst)
            date_str = now.strftime("%y-%m-%d")
            time_str = now.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
            
            # 채널 ID 선택
            if 유형 == "인첸트":
                channel_id = ENCHANT_LOG_CHANNEL_ID
                log_type_name = "인첸트 지급"
            else:  # 복구기록
                channel_id = ROLLBACK_LOG_CHANNEL_ID
                log_type_name = "롤백 복구"
            
            # 채널 가져오기
            channel = bot.get_channel(channel_id)
            if not channel:
                await ctx.respond(
                    embed=create_embed(
                        "❌ 오류",
                        f"기록 채널을 찾을 수 없습니다. (채널 ID: {channel_id})",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # 기록 메시지 생성
            if 유형 == "인첸트":
                log_message = f"{date_str} / {time_str} / {닉네임} / t-{티켓번호} / {내용}"
                content_label = "인첸트"
            else:
                log_message = f"{date_str} / {time_str} / {닉네임} / t-{티켓번호} / {내용}"
                content_label = "복구 좌표"

            # 임베드 생성
            embed = create_embed(
                "",
                ctx.user.mention + "\n" + log_message
            )

            await channel.send(embed=embed)
            
            # 성공 응답
            await ctx.respond(
        def setup(bot: discord.Bot) -> None:
                    f"✅ {log_type_name} 기록 완료",
                    f"**닉네임:** {닉네임}\n"
                    f"**티켓번호:** t-{티켓번호}\n"
                    f"**{content_label}:** {내용}\n"
                    f"**기록 시간:** {date_str} {time_str}",
                    discord.Color.green()
                ),
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"관리 기록 생성 오류: {e}", exc_info=True)
            await ctx.respond(
                embed=create_embed(
                    "❌ 오류",
                    f"기록 생성 중 오류가 발생했습니다: {str(e)}",
                    discord.Color.red()
                ),
                ephemeral=True
            )
