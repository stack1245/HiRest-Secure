"""HiRest Secure Bot - Server moderation and security bot."""
import asyncio
import logging
import discord

from utils.extension_loader import ExtensionLoader
from utils.logging import configure_logging
from utils.graceful_shutdown import setup_graceful_shutdown
from utils.constants import DEFAULT_ACTIVITY_NAME
from core.config import get_config

configure_logging()
logger = logging.getLogger(__name__)


class HiRestSecureBot(discord.Bot):
    """서버 보안 및 관리 봇."""
    
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.config = get_config()
        self.extension_loader = ExtensionLoader(self)
        self._commands_loaded = False
    
    async def on_ready(self) -> None:
        """봇 준비 완료 이벤트."""
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
        """명령어 오류 처리."""
        logger.error(f"명령어 오류: {ctx.command.name if ctx.command else '알 수 없음'} - {error}")
        
        try:
            if not ctx.response.is_done():
                await ctx.respond(f"오류가 발생했습니다: {error}", ephemeral=True)
        except Exception:
            pass
    
    async def sync_commands(self, **kwargs):
        """명령어 동기화."""
        try:
            if self.config.DEBUG_MODE and self.config.TARGET_GUILD_ID:
                guild_ids = [self.config.TARGET_GUILD_ID]
                for command in self.pending_application_commands:
                    if not command.guild_ids:
                        command.guild_ids = guild_ids
            
            await super().sync_commands(**kwargs)
        except Exception as e:
            logger.error(f"명령어 동기화 오류: {e}")


async def main():
    """봇 메인 진입점."""
    config = get_config()
    
    if not config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다")
        return
    
    bot = HiRestSecureBot()
    setup_graceful_shutdown()
    
    try:
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"예외 발생: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass