import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import discord

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 2000
DELETE_DELAY = 0.5

BAN_LOG_PATTERN = "## <:hr_ban:1350451179683057764> 차단 로그"


async def execute_cleanduplicates_action(
    player: Optional[str], 
    bot, 
    ctx: discord.ApplicationContext
) -> Dict[str, int]:
    from core.config import get_config
    
    config = get_config()
    
    try:
        # 길드 및 채널 확인
        guild = bot.get_guild(config.TARGET_GUILD_ID)
        if not guild:
            logger.error(f"길드를 찾을 수 없습니다: {config.TARGET_GUILD_ID}")
            return {}
        
        ban_log_channel = guild.get_channel(config.BAN_LOG_CHANNEL_ID)
        if not ban_log_channel:
            logger.error(f"차단 로그 채널을 찾을 수 없습니다: {config.BAN_LOG_CHANNEL_ID}")
            return {}
        
        if player:
            # 특정 플레이어의 중복 로그만 제거
            deleted_count = await _clean_player_duplicates(ban_log_channel, player)
            return {player: deleted_count} if deleted_count > 0 else {}
        else:
            # 모든 플레이어의 중복 로그 제거
            return await _clean_all_duplicates(ban_log_channel)
        
    except Exception as e:
        logger.error(f"중복 제거 중 오류 발생: {e}")
        return {}


async def _clean_player_duplicates(channel, player: str) -> int:
    # 대상 플레이어의 모든 차단 로그를 UUID별로 그룹화하여 수집
    uuid_groups = {}  # key: uuid, value: list of messages
    
    async for message in channel.history(limit=MAX_SEARCH_LIMIT):
        player_info = _extract_player_info(message)
        if player_info:
            nickname, uuid = player_info
            # 닉네임이 일치하는 경우만 수집
            if nickname.lower() == player.lower():
                if uuid not in uuid_groups:
                    uuid_groups[uuid] = []
                uuid_groups[uuid].append(message)
    
    # 각 UUID별로 중복 제거
    total_deleted = 0
    for uuid, messages in uuid_groups.items():
        if len(messages) > 1:
            duplicate_messages = _identify_duplicate_logs(messages)
            deleted_count = await _delete_duplicate_messages(duplicate_messages)
            total_deleted += deleted_count
    
    return total_deleted


async def _clean_all_duplicates(channel) -> Dict[str, int]:
    # 모든 차단 로그를 수집하고 (닉네임, UUID) 조합별로 그룹화
    player_messages = {}  # key: (nickname, uuid), value: list of messages
    async for message in channel.history(limit=MAX_SEARCH_LIMIT):
        player_info = _extract_player_info(message)
        if player_info:
            nickname, uuid = player_info
            key = f"{nickname}:{uuid}"
            if key not in player_messages:
                player_messages[key] = []
            player_messages[key].append(message)
    
    # 각 (닉네임, UUID) 조합별로 중복 제거
    deletion_results = {}
    for player_key, messages in player_messages.items():
        if len(messages) > 1:
            duplicate_messages = _identify_duplicate_logs(messages)
            deleted_count = await _delete_duplicate_messages(duplicate_messages)
            if deleted_count > 0:
                # 표시용으로 닉네임만 사용
                nickname = player_key.split(':')[0]
                if nickname in deletion_results:
                    deletion_results[nickname] += deleted_count
                else:
                    deletion_results[nickname] = deleted_count
    
    return deletion_results


def _extract_player_info(message: discord.Message) -> Optional[tuple[str, str]]:
    """
    메시지에서 플레이어 닉네임과 UUID를 추출합니다.
    
    Args:
        message: Discord 메시지
        
    Returns:
        Optional[tuple[str, str]]: (닉네임, UUID) 튜플, 추출 실패 시 None
    """
    import re
    
    if not message.content:
        return None
        
    # 차단 로그 패턴 확인
    if BAN_LOG_PATTERN not in message.content:
        return None
    
    # 닉네임 추출 (백틱으로 감싸진 첫 번째 값)
    nickname_match = re.search(r'`([^`]+)`', message.content)
    if not nickname_match:
        return None
    nickname = nickname_match.group(1)
    
    # UUID 추출 (UUID 형식: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', message.content, re.IGNORECASE)
    if not uuid_match:
        return None
    uuid = uuid_match.group(1)
    
    return (nickname, uuid)


def _is_target_ban_log(message: discord.Message, player: str) -> bool:
    if not message.content:
        return False
        
    # 차단 로그 패턴 확인
    if BAN_LOG_PATTERN not in message.content:
        return False
    
    # 플레이어명 확인 (백틱으로 감싸진 형태)
    return f"`{player}`" in message.content


def _identify_duplicate_logs(messages: List[discord.Message]) -> List[discord.Message]:
    """
    중복 로그를 식별합니다. 최초 로그는 보존하고 나머지를 중복으로 간주합니다.
    
    Args:
        messages: 차단 로그 메시지 목록
        
    Returns:
        List[discord.Message]: 삭제할 중복 메시지 목록
    """
    # 생성일시 기준 오름차순 정렬 (가장 오래된 것이 첫 번째)
    sorted_messages = sorted(messages, key=lambda x: x.created_at)
    
    # 첫 번째(최초) 로그는 보존하고 나머지는 중복으로 간주
    return sorted_messages[1:] if len(sorted_messages) > 1 else []


async def _delete_duplicate_messages(duplicate_messages: List[discord.Message]) -> int:
    """
    중복 메시지들을 삭제합니다.
    
    Args:
        duplicate_messages: 삭제할 중복 메시지 목록
        
    Returns:
        int: 삭제된 메시지 개수
    """
    deleted_count = 0
    
    for message in duplicate_messages:
        try:
            await message.delete()
            deleted_count += 1
            await asyncio.sleep(DELETE_DELAY)  # API 제한 방지
        except discord.NotFound:
            continue
        except Exception as e:
            logger.error(f"메시지 삭제 실패 (ID: {message.id}): {e}")
            continue
    
    return deleted_count


async def handle_cleanduplicates_command(
    ctx: discord.ApplicationContext, 
    player: Optional[str]
) -> None:
    """
    중복 제거 명령어 처리 로직
    
    Args:
        ctx: Discord 상호작용 객체
        player: 대상 플레이어명 (None이면 모든 플레이어)
    """
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "cleanduplicates", 
            {"player": player, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 처리 중 메시지 표시
    if player:
        description = f"**`{player}`**님의 중복 차단 로그를 정리하고 있습니다..."
    else:
        description = "**모든 플레이어**의 중복 차단 로그를 정리하고 있습니다..."
    
    processing_embed = create_embed(
        title="🧹 중복 제거 중...",
        description=f"{description}\n⚠️ 닉네임과 UUID를 식별하여 각 플레이어의 최초 로그는 보존되고 중복 로그만 제거됩니다.",
        color=0xF39C12,
        ctx=ctx
    )
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 중복 제거 실행
    deletion_results = await execute_cleanduplicates_action(player, ctx.bot, ctx)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_cleanup_result_embed(ctx, player, deletion_results)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    total_deleted = sum(deletion_results.values()) if deletion_results else 0
    await command_logger.log_command_usage(
        ctx, 
        "cleanduplicates", 
        {"player": player or "all", "deleted_count": total_deleted}, 
        success=True
    )


def _create_cleanup_result_embed(
    ctx: discord.ApplicationContext,
    player: Optional[str],
    deletion_results: Dict[str, int]
) -> discord.Embed:
    """
    중복 제거 결과 임베드를 생성합니다.
    
    Args:
        ctx: Discord 상호작용 객체
        player: 대상 플레이어명 (None이면 모든 플레이어)
        deletion_results: 플레이어별 삭제된 중복 로그 개수
        
    Returns:
        discord.Embed: 중복 제거 결과 임베드
    """
    total_deleted = sum(deletion_results.values()) if deletion_results else 0
    
    if total_deleted > 0:
        if player:
            # 특정 플레이어만 제거한 경우
            embed = create_embed(
                title="🧹 중복 제거 완료",
                description=f"**`{player}`**님의 중복 차단 로그 **{total_deleted}건**을 성공적으로 제거했습니다.",
                color=0x27AE60,
                ctx=ctx,
                success=True
            )
            
            embed.add_field(
                name="📋 정리 내용",
                value=f"• 최초 로그: **보존됨**\n• 중복 로그: **{total_deleted}건 제거됨**",
                inline=False
            )
        else:
            # 모든 플레이어의 중복 제거
            player_count = len(deletion_results)
            embed = create_embed(
                title="🧹 중복 제거 완료",
                description=f"**{player_count}명**의 플레이어에 대해 중복 차단 로그 **{total_deleted}건**을 성공적으로 제거했습니다.",
                color=0x27AE60,
                ctx=ctx,
                success=True
            )
            
            # 플레이어별 제거 내역 (최대 10명까지만 표시)
            details = []
            for idx, (p_name, count) in enumerate(sorted(deletion_results.items(), key=lambda x: x[1], reverse=True)):
                if idx < 10:
                    details.append(f"• `{p_name}`: **{count}건**")
                elif idx == 10:
                    details.append(f"• 외 {len(deletion_results) - 10}명...")
                    break
            
            embed.add_field(
                name="📋 정리 내용",
                value="\n".join(details) if details else "• 없음",
                inline=False
            )
        
        embed.add_field(
            name="✅ 완료 상태",
            value="로그 채널이 정리되어 가독성이 향상되었습니다.",
            inline=False
        )
    else:
        if player:
            description = f"**`{player}`**님의 중복 차단 로그가 발견되지 않았습니다."
        else:
            description = "중복 차단 로그가 발견되지 않았습니다."
            
        embed = create_embed(
            title="🧹 중복 제거 결과",
            description=description,
            color=0x95A5A6,
            ctx=ctx,
            success=True
        )
        
        embed.add_field(
            name="📋 확인 결과",
            value="• 중복 로그 없음\n• 정리가 필요하지 않음\n• 이미 깔끔한 상태입니다",
            inline=False
        )
    
    if player:
        embed.add_field(name="🎮 대상 플레이어", value=f"`{player}`", inline=False)
    else:
        embed.add_field(name="🎮 대상 플레이어", value="전체", inline=False)
    
    embed.add_field(name="👤 실행자", value=ctx.user.mention, inline=False)
    
    return embed


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="중복제거", description="플레이어의 중복 차단 로그를 제거합니다.")
    async def cleanduplicates_func(
        ctx: discord.ApplicationContext,
        player: Optional[str] = discord.Option(str, description="중복 로그를 제거할 플레이어 이름 (비워두면 전체)", default=None, required=False)
    ):
        """플레이어의 중복 차단 로그 제거."""
        await handle_cleanduplicates_command(ctx, player)