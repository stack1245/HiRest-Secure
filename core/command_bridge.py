import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from .config import get_config

config = get_config()
logger = logging.getLogger(__name__)


class CommandBridge:

    @staticmethod
    async def get_channel(bot: commands.Bot, channel_id: int, guild_id: int) -> Optional[discord.TextChannel]:
        try:
            guild = bot.get_guild(guild_id)
            if not guild:
                return None
            
            channel = guild.get_channel(channel_id)
            return channel if isinstance(channel, discord.TextChannel) else None
        except Exception:
            return None

    @staticmethod
    async def send_command(
        bot: commands.Bot,
        command: str,
        channel_id: int,
        guild_id: int,
        executor: Optional[str] = None,
        silent: bool = False
    ) -> bool:
        if not command or not command.strip():
            return False

        try:
            channel = await CommandBridge.get_channel(bot, channel_id, guild_id)
            if not channel:
                return False

            await channel.send(command.strip())
            return True
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return False
        except Exception as e:
            logger.error(f"명령어 전송 실패: {e}")
            return False

    @staticmethod
    async def send_proxy_command(bot: commands.Bot, command: str, ctx: discord.ApplicationContext) -> bool:
        return await CommandBridge.send_command(
            bot,
            f".p {command}",
            config.API_REQUEST_CHANNEL_ID,
            config.TARGET_GUILD_ID,
            executor=ctx.user.mention
        )

    @staticmethod
    async def send_ilunar_command(bot: commands.Bot, command: str, ctx: discord.ApplicationContext) -> bool:
        return await CommandBridge.send_command(
            bot,
            f".s ilunar {command}",
            config.API_REQUEST_CHANNEL_ID,
            config.TARGET_GUILD_ID,
            executor=ctx.user.mention
        )

    @staticmethod
    async def send_console_command(bot: commands.Bot, command: str, executor: str, silent: bool = False) -> bool:
        if not config.ILUNAR_CONSOLE_CHANNEL_ID:
            return False
        
        return await CommandBridge.send_command(
            bot, command,
            config.ILUNAR_CONSOLE_CHANNEL_ID,
            config.TARGET_GUILD_ID,
            executor=executor,
            silent=silent
        )


async def send_proxy_command(bot: commands.Bot, command: str, ctx: discord.ApplicationContext) -> bool:
    return await CommandBridge.send_proxy_command(bot, command, ctx)


async def send_ilunar_command(bot: commands.Bot, command: str, ctx: discord.ApplicationContext) -> bool:
    return await CommandBridge.send_ilunar_command(bot, command, ctx)


async def send_console_command(bot: commands.Bot, command: str, executor: str, silent: bool = False) -> bool:
    return await CommandBridge.send_console_command(bot, command, executor, silent)
