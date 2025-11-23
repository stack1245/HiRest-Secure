import asyncio
import logging
from typing import Any, Dict, List, Optional

import discord

from utils.decorators import check_staff_permission
from utils.utils import CommandLogger, create_embed

logger = logging.getLogger(__name__)

MAX_COMMAND_LENGTH = 500
MAX_SERVER_NAME_LENGTH = 10

SUPPORTED_SERVERS = ["ilunar", "proxy"]

DANGEROUS_COMMANDS = [
    "stop",
    "restart",
    "shutdown",
    "ban",
    "whitelist",
    "op",
    "deop",
    "kill",
    "clear",
    "delete",
    "remove",
]


class CommandModal(discord.ui.Modal, title="서버 명령어 실행"):
    
    def __init__(self) -> None:
        super().__init__()
        
    server_type = discord.ui.TextInput(
        label="서버 선택",
        placeholder="ilunar 또는 proxy 입력",
        required=True,
        max_length=MAX_SERVER_NAME_LENGTH
    )
    
    command = discord.ui.TextInput(
        label="명령어",
        placeholder="실행할 명령어를 입력하세요 (예: list, help)",
        required=True,
        max_length=MAX_COMMAND_LENGTH,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, ctx: discord.ApplicationContext) -> None:
        from core.command_bridge import send_ilunar_command, send_proxy_command, send_console_command
        
        cmd_logger = CommandLogger()
        
        server = self.server_type.value.lower().strip()
        cmd = self.command.value.strip()
        
        validation_result = _validate_server_and_command(server, cmd)
        if not validation_result["valid"]:
            await cmd_logger.log_command_usage(
                ctx, 
                "command", 
                {"server_type": server, "command": cmd, "error": validation_result["error"]}, 
                success=False
            )
            
            error_embed = _create_validation_error_embed(
                ctx, validation_result["error"]
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
            return
        
        if _is_dangerous_command(cmd):
            warning_embed = _create_danger_warning_embed(ctx, cmd, server)
            await ctx.respond(embed=warning_embed, ephemeral=True)
            return
        
        processing_embed = _create_processing_embed(ctx, server)
        await ctx.defer(ephemeral=False)
        await ctx.edit(embed=processing_embed)
        
        try:
            success = await _execute_server_command(server, cmd, ctx)
            
            await cmd_logger.log_command_usage(
                ctx, 
                "command", 
                {"server_type": server, "command": cmd}, 
                success=success
            )
            
            result_embed = _create_command_result_embed(ctx, server, cmd, success)
            await ctx.edit(embed=result_embed)
            
        except Exception as e:
            await cmd_logger.log_command_usage(
                ctx, 
                "command", 
                {"server_type": server, "command": cmd, "error": str(e)}, 
                success=False
            )
            
            error_embed = _create_execution_error_embed(ctx, str(e))
            await ctx.edit(embed=error_embed)


def _validate_server_and_command(server: str, command: str) -> Dict[str, Any]:
    if server not in SUPPORTED_SERVERS:
        return {
            "valid": False,
            "error": f"서버는 `{', '.join(SUPPORTED_SERVERS)}`만 선택할 수 있습니다."
        }
    
    if not command.strip():
        return {
            "valid": False,
            "error": "명령어를 입력해주세요."
        }
    
    if len(command) > MAX_COMMAND_LENGTH:
        return {
            "valid": False,
            "error": f"명령어는 최대 {MAX_COMMAND_LENGTH}글자까지 입력할 수 있습니다."
        }
    
    return {"valid": True, "error": None}


def _is_dangerous_command(command: str) -> bool:
    command_lower = command.lower().strip()
    return any(danger in command_lower for danger in DANGEROUS_COMMANDS)


async def _execute_server_command(server: str, command: str, ctx: discord.ApplicationContext) -> bool:
    from core.command_bridge import send_console_command, send_proxy_command
    
    if server == "ilunar":
        return await send_console_command(
            ctx.bot, command, ctx.user.mention
        )
    elif server == "proxy":
        return await send_proxy_command(
            ctx.bot, command, ctx
        )
    
    return False


def _create_validation_error_embed(ctx: discord.ApplicationContext, error: str) -> discord.Embed:
    return create_embed(
        title="❌ 입력 오류",
        description=f"입력된 정보가 올바르지 않습니다.\n\n**오류**: {error}",
        color=0xE74C3C,
        ctx=ctx,
        success=False
    )


def _create_danger_warning_embed(
    ctx: discord.ApplicationContext, 
    command: str, 
    server: str
) -> discord.Embed:
    return create_embed(
        title="위험한 명령어 감지",
        description=f"**{command}**는 서버에 영향을 줄 수 있는 위험한 명령어입니다.\n\n"
                   f"**대상 서버**: `{server}`\n"
                   f"**명령어**: `{command}`\n\n"
                   f"실행하시려면 다시 한 번 명령어를 입력해주세요.",
        color=0xFF6B35,
        success=False
    )


def _create_processing_embed(ctx: discord.ApplicationContext, server: str) -> discord.Embed:
    return create_embed(
        title="명령어 실행 중...",
        description=f"**{server}** 서버에 명령어를 전송하고 있습니다...",
        color=0xF39C12
    )


def _create_command_result_embed(
    ctx: discord.ApplicationContext,
    server: str,
    command: str,
    success: bool
) -> discord.Embed:
    if success:
        embed = create_embed(
            title="명령어 실행됨",
            description=f"**{server}** 서버에 명령어를 성공적으로 전송했습니다.",
            success=True
        )
    else:
        embed = create_embed(
            title="명령어 실행 실패",
            description=f"**{server}** 서버에 명령어 전송을 실패했습니다.",
            success=False
        )
    
    embed.add_field(name="🖥️ 서버", value=f"`{server}`", inline=True)
    embed.add_field(name="📝 명령어", value=f"`{command}`", inline=False)
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def _create_execution_error_embed(ctx: discord.ApplicationContext, error: str) -> discord.Embed:
    return create_embed(
        title="명령어 실행 오류",
        description=f"명령어 실행 중 오류가 발생했습니다.\n\n**오류**: {error}",
        success=False
    )


def _create_permission_error_embed(ctx: discord.ApplicationContext) -> discord.Embed:
    return create_embed(
        title="권한 부족",
        description="이 명령어를 사용할 권한이 없습니다.\n**필요 권한**: `스탭`",
        success=False
    )


async def handle_command_command(ctx: discord.ApplicationContext) -> None:
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, "command", {"error": "권한 부족"}, success=False
        )
        return
    
    modal = CommandModal()
    await ctx.response.send_modal(modal)


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="command", description="서버에 직접 명령어를 실행합니다.")
    async def command_func(ctx: discord.ApplicationContext):
        """서버에 직접 명령어 실행."""
        await handle_command_command(ctx)
    
    bot.tree.add_command(command_func)