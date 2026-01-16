"""권한 확인 및 데코레이터"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from core.config import get_config
from utils.utils import create_embed

if TYPE_CHECKING:
    pass


async def check_staff_permission(ctx: discord.ApplicationContext) -> bool:
    """스탭 권한 확인.
    
    Args:
        ctx: 명령어 컨텍스트
        
    Returns:
        스탭 권한 여부
    """
    if not isinstance(ctx.user, discord.Member):
        await ctx.respond("서버 전용 명령어입니다.", ephemeral=True)
        return False
    
    config = get_config()
    has_permission = any(role.id == config.STAFF_ROLE_ID for role in ctx.user.roles)
    
    if not has_permission:
        embed = create_embed(title="", description="스탭 권한이 필요합니다.", success=False)
        await ctx.respond(embed=embed, ephemeral=True)
    
    return has_permission
