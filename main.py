"""HiRest 보안 봇"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional
import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.constants import DEFAULT_ACTIVITY_NAME
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging import configure_logging
from core.config import get_config

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


class HiRestSecureBot(discord.Bot):
    """서버 보안 및 모더레이션"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        
        self.config = get_config()
        self.extension_loader = ExtensionLoader(self)
        self._commands_loaded = False
        self._auto_save_task: Optional[asyncio.Task] = None
    
    async def on_ready(self) -> None:
        """봇 준비 완료"""
        if not self.user:
            return
        
        if not self._commands_loaded:
            try:
                if not self.config.validate_config():
                    logger.error("설정 검증 실패")
                    await self.close()
                    return
                
                self.extension_loader.load_all_extensions("commands")
                self.extension_loader.load_all_extensions("uncommands")
                await self.sync_commands()
                self._commands_loaded = True
                print(f"[{self.user.name}] 준비 완료")
            except Exception as e:
                logger.error(f"초기화 실패: {e}")
                return
        
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Game(name=DEFAULT_ACTIVITY_NAME)
            )
        except Exception as e:
            logger.error(f"상태 변경 실패: {e}")
    
    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        error: discord.DiscordException
    ) -> None:
        """명령어 오류 처리"""
        logger.error(f"명령어 오류: {ctx.command.name if ctx.command else '알 수 없음'} - {error}")
        
        try:
            if not ctx.response.is_done():
                await ctx.respond(f"오류가 발생했습니다: {error}", ephemeral=True)
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
        if self._auto_save_task:
            self._auto_save_task.cancel()
        await super().close()


def main():
    """봇 실행"""
    config = get_config()
    if not config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다.")
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
    finally:
        logger.info("봇 종료됨")


if __name__ == "__main__":
    main()