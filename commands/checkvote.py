"""추천 정보 확인 명령어."""
import asyncio
import logging
from typing import Dict, Any, Optional
import discord

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission

logger = logging.getLogger(__name__)


async def check_vote_info_async(vote_id: str, server_id: str = "16262-ilunar.kr") -> Dict[str, str]:
    """추천 정보 비동기 조회."""
    url = f"https://minelist.kr/servers/{server_id}/votes/{vote_id}"
    
    driver = None
    try:
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 비동기 실행을 위해 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _fetch_vote_info, url, chrome_options)
        return result
        
    except Exception as e:
        logger.error(f"추천 정보 조회 오류: {e}")
        return {
            "status": "error",
            "error": str(e),
            "vote_id": vote_id
        }


def _fetch_vote_info(url: str, chrome_options: Options) -> Dict[str, str]:
    """추천 정보 페치 (동기 실행)."""
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 404 페이지 체크
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if '404' in title_text or '찾을 수 없' in title_text:
                return {
                    "status": "not_found",
                    "error": "해당 추천 고유번호를 찾을 수 없습니다."
                }
        
        # 추천 성공 여부 확인
        success = '추천이 성공하였습니다' in page_source or '추천 성공' in page_source
        
        # 정보 추출
        game_id = "N/A"
        vote_time = "N/A"
        server_name = "N/A"
        
        # 방법 1: tbody > tr > td 구조
        tbody = soup.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if '게임 아이디' in label or '계임 아이디' in label or '아이디' in label:
                        game_id = value
                    elif '추천 시간' in label or '시간' in label:
                        vote_time = value
                    elif '추천한 서비' in label or '서버' in label:
                        server_name = value
        
        # 방법 2: 모든 테이블 행 검색
        if game_id == "N/A" or vote_time == "N/A" or server_name == "N/A":
            all_rows = soup.find_all('tr')
            for row in all_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if '게임 아이디' in label or '계임 아이디' in label or '아이디' in label:
                        game_id = value
                    elif '추천 시간' in label or '시간' in label:
                        vote_time = value
                    elif '추천한 서비' in label or '서버' in label:
                        server_name = value
        
        # 방법 3: 텍스트에서 직접 검색
        if game_id == "N/A" or vote_time == "N/A" or server_name == "N/A":
            all_text = soup.get_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                if ('게임 아이디' in line or '계임 아이디' in line) and i + 1 < len(lines):
                    if game_id == "N/A":
                        game_id = lines[i + 1]
                elif '추천 시간' in line and i + 1 < len(lines):
                    if vote_time == "N/A":
                        vote_time = lines[i + 1]
                elif '추천한 서비' in line and i + 1 < len(lines):
                    if server_name == "N/A":
                        server_name = lines[i + 1]
        
        return {
            "status": "success" if success else "unknown",
            "game_id": game_id,
            "vote_time": vote_time,
            "server_name": server_name
        }
        
    finally:
        if driver:
            driver.quit()


def _create_processing_embed(ctx: discord.ApplicationContext, vote_id: str) -> discord.Embed:
    return create_embed(
        title="🔍 추천 정보 조회 중...",
        description=f"추천 고유번호 **`{vote_id}`**의 정보를 조회하고 있습니다...",
        color=0xF39C12,
        ctx=ctx
    )


def _create_result_embed(
    ctx: discord.ApplicationContext,
    vote_id: str,
    result: Dict[str, str]
) -> discord.Embed:
    status = result.get("status")
    
    if status == "error":
        embed = create_embed(
            title="❌ 조회 오류",
            description=f"추천 정보 조회 중 오류가 발생했습니다.\n\n**오류**: {result.get('error', '알 수 없는 오류')}",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    elif status == "not_found":
        embed = create_embed(
            title="❌ 추천 정보 없음",
            description=f"해당 추천 고유번호를 찾을 수 없습니다.\n\n**추천 고유번호**: `{vote_id}`",
            color=0xE74C3C,
            ctx=ctx,
            success=False
        )
    else:
        embed = create_embed(
            title="✅ 추천 정보 조회 완료",
            description="추천 정보를 성공적으로 조회했습니다.",
            color=0x00FF00,
            ctx=ctx,
            success=True
        )
        
        # 정보 필드 추가
        embed.add_field(name="🔢 추천 고유번호", value=f"`{vote_id}`", inline=False)
        embed.add_field(name="🎮 게임 아이디", value=f"`{result.get('game_id', 'N/A')}`", inline=False)
        embed.add_field(name="🕐 추천 시간", value=f"`{result.get('vote_time', 'N/A')}`", inline=False)
        embed.add_field(name="🖥️ 추천한 서버", value=f"`{result.get('server_name', 'N/A')}`", inline=False)
        embed.add_field(name="👤 조회자", value=ctx.user.mention, inline=False)
    
    return embed


async def handle_checkvote_command(
    ctx: discord.ApplicationContext, 
    vote_id: str,
    server_id: Optional[str] = None
) -> None:
    command_logger = CommandLogger()
    
    # 권한 체크
    if not await check_staff_permission(ctx):
        await command_logger.log_command_usage(
            ctx, 
            "checkvote", 
            {"vote_id": vote_id, "error": "권한 부족"}, 
            success=False
        )
        return
    
    # 서버 ID 기본값 설정
    if not server_id:
        server_id = "16262-ilunar.kr"
    
    # 처리 중 메시지 표시
    processing_embed = _create_processing_embed(ctx, vote_id)
    await ctx.defer(ephemeral=False)
    await ctx.edit(embed=processing_embed)
    
    # 추천 정보 조회 실행
    result = await check_vote_info_async(vote_id, server_id)
    
    # 결과 임베드 생성 및 전송
    result_embed = _create_result_embed(ctx, vote_id, result)
    await ctx.edit(embed=result_embed)
    
    # 결과 로깅
    success = result.get("status") not in ["error", "not_found"]
    await command_logger.log_command_usage(
        ctx, 
        "checkvote", 
        {"vote_id": vote_id, "server_id": server_id, "result": result}, 
        success=success
    )


def setup(bot):
    """명령어 등록."""
    
    @bot.slash_command(name="checkvote", description="마인리스트 추천 고유번호로 추천 정보를 조회합니다.")
    async def checkvote_func(
        ctx: discord.ApplicationContext, 
        vote_id: str,
        server_id: Optional[str] = None
    ):
        """추천 정보 조회."""
        await handle_checkvote_command(ctx, vote_id, server_id)