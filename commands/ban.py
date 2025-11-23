import asyncio
import logging
from typing import Dict, Tuple

import discord

from core.command_bridge import send_console_command, send_proxy_command
from core.config import get_config
from utils.constants import ban_reason_autocomplete, INFO_DELAY
from utils.decorators import check_staff_permission
from utils.utils import CommandLogger, create_embed

logger = logging.getLogger(__name__)
MIN_NAME_LEN = 3


async def execute_ban_action(
    player: str, reason: str, bot, ctx: discord.ApplicationContext
) -> Tuple[bool, Dict[str, str]]:
    config = get_config()
    
    try:
        if not await send_proxy_command(bot, f"ban {player} {reason}", ctx):
            return False, {"error": "차단 명령어 전송 실패"}
        
        player_info = await _collect_player_info(player, bot, ctx, config)
        ban_log_link = await _upload_ban_log(config, bot, player_info, reason)
        player_info["ban_log_link"] = ban_log_link
        
        return True, player_info
    except Exception as e:
        logger.error(f"차단 오류: {e}")
        return False, {"error": str(e)}


async def _collect_player_info(
    player: str,
    bot,
    ctx: discord.ApplicationContext,
    config,
    max_retries: int = 2
) -> Dict[str, str]:
    from utils.utils import ConsoleResponseHandler, parse_player_info
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"플레이어 정보 재수집 시도 {attempt + 1}/{max_retries}: {player}")
            
            # 콘솔 명령어 전송
            if not await send_console_command(
                bot, 
                f"cmi info {player}", 
                ctx.user.mention, 
                silent=True
            ):
                if attempt == max_retries - 1:
                    logger.warning(f"플레이어 정보 조회 명령어 전송 실패: {player}")
                    continue
                await asyncio.sleep(1)
                continue
            
            # 응답 대기 시간 증가 (첫 시도: 5초, 재시도: 7초)
            wait_time = INFO_DELAY + 2.0 + (attempt * 2.0)
            await asyncio.sleep(INFO_DELAY)
            
            response_handler = ConsoleResponseHandler(
                bot, 
                config.ILUNAR_CONSOLE_CHANNEL_ID
            )
            
            # 키워드를 더 포괄적으로 설정 (Prefix, UUID, Ip 등)
            keywords = [player, "UUID:", "Ip:", "Prefix:", "PlayTime:"]
            console_response = await response_handler.wait_for_response(
                ctx.user.mention, 
                timeout=wait_time,
                keywords=keywords
            )
            
            if console_response:
                logger.info(f"콘솔 응답 수신 (시도 {attempt + 1}, 길이: {len(console_response)}자)")
                logger.debug(f"응답 내용 (첫 200자): {console_response[:200]}")
                
                player_info = parse_player_info(console_response, player)
                
                if player_info:
                    has_uuid = player_info.get("uuid") is not None
                    has_ip = player_info.get("ip") is not None
                    
                    logger.info(
                        f"파싱 결과: {player} | "
                        f"UUID: {'✓ ' + player_info.get('uuid', '')[:8] + '...' if has_uuid else '✗'} | "
                        f"IP: {'✓ ' + player_info.get('ip', '') if has_ip else '✗'}"
                    )
                    
                    # UUID나 IP 중 하나라도 있으면 성공
                    if has_uuid or has_ip:
                        if not has_uuid:
                            player_info["uuid"] = "알 수 없음"
                        if not has_ip:
                            player_info["ip"] = "알 수 없음"
                        return player_info
                    else:
                        logger.warning(f"UUID/IP 모두 누락: {player}")
                else:
                    logger.warning(f"파싱 실패 (시도 {attempt + 1}): {player}")
            else:
                logger.warning(f"콘솔 응답 없음 (시도 {attempt + 1}): {player}")
            
            # 마지막 시도가 아니면 잠시 대기 후 재시도
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
        
        except Exception as e:
            logger.error(f"플레이어 정보 수집 중 오류 (시도 {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                break
    
    # 모든 시도 실패 시 기본값 반환
    logger.warning(f"플레이어 정보 수집 최종 실패, 기본값 사용: {player}")
    return {
        "username": player,
        "uuid": "알 수 없음",
        "ip": "알 수 없음"
    }


async def _upload_ban_log(
    config, 
    bot, 
    player_info: Dict[str, str], 
    reason: str
) -> str:
    if not config.BAN_LOG_CHANNEL_ID:
        return None
    
    try:
        guild = bot.get_guild(config.TARGET_GUILD_ID)
        if not guild:
            logger.warning(f"길드를 찾을 수 없음 (ID: {config.TARGET_GUILD_ID})")
            return None
        
        ban_log_channel = guild.get_channel(config.BAN_LOG_CHANNEL_ID)
        if not ban_log_channel:
            logger.warning(
                f"차단 로그 채널을 찾을 수 없음 "
                f"(ID: {config.BAN_LOG_CHANNEL_ID})"
            )
            return None
        
        # UUID와 IP 표시 형식 (알 수 없는 경우 처리)
        uuid_display = player_info.get('uuid', '알 수 없음')
        if uuid_display == "알 수 없음":
            uuid_display = "`알 수 없음` ⚠️"
        else:
            uuid_display = uuid_display
        
        ip_display = player_info.get('ip', '알 수 없음')
        if ip_display == "알 수 없음":
            ip_display = "`알 수 없음` ⚠️"
        else:
            ip_display = ip_display
        
        log_message = f"""## <:hr_ban:1350451179683057764> 차단 로그

`Username` `{player_info['username']}`
`UUID` {uuid_display}
`IP` {ip_display}
`차단 사유` {reason}"""
        
        sent_message = await ban_log_channel.send(log_message)
        return sent_message.jump_url
        
    except Exception as e:
        logger.error(f"차단 로그 업로드 실패: {e}")
        return None


async def handle_ban_command(
    ctx: discord.ApplicationContext, 
    player: str, 
    reason: str = "사유 없음"
) -> None:
    command_logger = CommandLogger()
    
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx,
            "ban",
            {"player": player, "reason": reason, "error": "권한 부족"},
            success=False
        )
        return
    
    player = player.strip()
    reason = reason.strip() if reason else "사유 없음"
    
    if len(player) < MIN_NAME_LEN:
        embed = create_embed(
            title="입력 오류",
            description="플레이어 이름은 3자 이상이어야 합니다.",
            success=False
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    
    processing_embed = create_embed(
        title="차단 처리 중...",
        description=f"**`{player}`**님을 차단하고 차단 로그를 업로드하고 있습니다...",
        color=0xF39C12
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    success, player_info = await execute_ban_action(
        player, 
        reason, 
        ctx.bot, 
        ctx
    )
    
    await command_logger.log_command_usage(
        ctx,
        "ban",
        {
            "player": player,
            "reason": reason,
            "player_info": player_info if success else None
        },
        success=success
    )
    
    result_embed = _create_result_embed(
        player, reason, success, player_info, ctx
    )
    await ctx.edit(embed=result_embed)


def _create_result_embed(
    player: str,
    reason: str,
    success: bool,
    player_info: Dict[str, str],
    ctx: discord.ApplicationContext
) -> discord.Embed:
    if success:
        embed = create_embed(
            title="차단 완료",
            description=(
                f"**`{player}`**님이 성공적으로 차단되었고 "
                f"차단 로그가 업로드되었습니다."
            ),
            success=True
        )
        
        log_info = (
            f"[차단 로그 메시지로 이동]({player_info['ban_log_link']})" 
            if player_info.get('ban_log_link') 
            else "차단 로그 채널에 업로드 완료"
        )
        embed.add_field(
            name="📋 차단 로그 정보", 
            value=log_info, 
            inline=False
        )
        
        embed.add_field(
            name="🎮 플레이어", 
            value=f"`{player}`", 
            inline=False
        )
        embed.add_field(
            name="🆔 UUID", 
            value=f"`{player_info['uuid']}`", 
            inline=False
        )
        embed.add_field(
            name="🌐 IP", 
            value=f"`{player_info['ip']}`", 
            inline=False
        )
    else:
        error_detail = (
            player_info.get('error', '알 수 없는 오류') 
            if player_info 
            else '알 수 없는 오류'
        )
        embed = create_embed(
            title="차단 실패",
            description=(
                f"**`{player}`**님의 차단 처리 중 오류가 발생했습니다.\n\n"
                f"**오류 내용**: {error_detail}"
            ),
            success=False
        )
    
    embed.add_field(name="📝 사유", value=f"`{reason}`", inline=False)
    embed.add_field(
        name="👤 실행자", 
        value=ctx.user.mention, 
        inline=False
    )
    
    return embed


def setup(bot) -> None:
    @bot.slash_command(name="ban", description="플레이어를 차단합니다.")
    async def ban_func(
        ctx: discord.ApplicationContext,
        player: str = discord.Option(str, description="차단할 플레이어 이름"),
        reason: str = discord.Option(str, description="차단 사유", default="사유 없음", autocomplete=ban_reason_autocomplete)
    ) -> None:
        await handle_ban_command(ctx, player, reason)