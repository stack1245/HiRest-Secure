"""HiRest 보안 모더레이션 봇"""
from __future__ import annotations
import asyncio
import os
import sys

import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.constants import DEFAULT_ACTIVITY_NAME
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging
from core.config import get_config

load_dotenv()
configure_logging()

import logging
logger = logging.getLogger(__name__)


class HiRestSecureBot(discord.Bot):
    """서버 보안, 모더레이션 및 관리"""

    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(intents=intents)

        self.config = get_config()
        self.extension_loader = ExtensionLoader(self)
        self._initialized = False
        self._auto_save_task: asyncio.Task | None = None
    
    async def on_ready(self) -> None:
        """봇 준비 완료"""
        if self._initialized or not self.user:
            return
        
        try:
            await self._initialize()
            self._initialized = True
            print(f"[{self.user.name}] 준비 완료")
        except Exception as e:
            logger.error(f"초기화 실패: {e}", exc_info=e)
            await self.close()
    
    async def _initialize(self) -> None:
        """초기화 로직"""
        if not self.config.validate_config():
            raise RuntimeError("설정 검증 실패")
        
        self.extension_loader.load_extension_groups("commands")
        self.extension_loader.load_extension_groups("uncommands")
        if self.extension_loader.failed_extensions:
            for ext_name, error in self.extension_loader.failed_extensions:
                logger.error(f"명령어 로드 실패: {ext_name}\n{error}")
        
        await self.sync_commands()
        
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Game(name=DEFAULT_ACTIVITY_NAME)
            )
        except Exception as e:
            logger.error(f"상태 변경 오류: {e}")
    
    async def on_application_command_error(
        self,
        context: discord.ApplicationContext,
        error: discord.DiscordException
    ) -> None:
        """명령어 오류 처리"""
        logger.error(f"명령어 오류: {error}", exc_info=error)

        try:
            embed = discord.Embed(
                description=f"오류 발생: {str(error)[:100]}",
                color=0xE74C3C
            )
            if not context.response.is_done():
                await context.respond(embed=embed, ephemeral=True)
        except Exception:
            pass
    
    async def sync_commands(self, **kwargs) -> None:
        """명령어 동기화"""
        try:
            if self.config.DEBUG_MODE and self.config.TARGET_GUILD_ID:
                guild_ids = [self.config.TARGET_GUILD_ID]
                for command in self.pending_application_commands:
                    if not command.guild_ids:
                        command.guild_ids = guild_ids
            await super().sync_commands(**kwargs)
        except Exception as e:
            logger.error(f"명령어 동기화 오류: {e}")
    
    async def close(self) -> None:
        """봇 종료 처리"""
        if self._auto_save_task and not self._auto_save_task.done():
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
        
        await super().close()


def main() -> None:
    """봇 실행"""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    config = get_config()
    if not config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN 미설정")
        return

    bot = HiRestSecureBot()

    def shutdown_handler():
        asyncio.create_task(bot.close())

    register_shutdown_callback(shutdown_handler)
    setup_graceful_shutdown()

    try:
        bot.run(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()