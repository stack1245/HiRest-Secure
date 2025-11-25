"""Permission decorators and checks."""
import discord

from core.config import get_config
from utils.utils import create_embed


async def check_staff_permission(ctx: discord.ApplicationContext) -> bool:
    """스탭 권한 확인."""
    if not isinstance(ctx.user, discord.Member):
        await ctx.respond("서버 전용 명령어입니다.", ephemeral=True)
        return False
    
    config = get_config()
    has_permission = any(role.id == config.STAFF_ROLE_ID for role in ctx.user.roles)
    
    if not has_permission:
        embed = create_embed(title="", description="스탭 권한이 필요합니다.", success=False)
        await ctx.respond(embed=embed, ephemeral=True)
    
    return has_permission
