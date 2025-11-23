# HiRest Secure Bot

마인크래프트 서버 보안/플레이어 관리/로그 시스템을 위한 Discord 봇.
## 특징 (표준화 적용)
- 최소 로그 & 통합 에러 처리
- 자동 명령어 로더 / 상수 / Graceful Shutdown
- 플레이어 제재/정보/추천 조회/로그 관리 통합
## 환경 변수 (.env)
```env
 DISCORD_TOKEN=your_discord_bot_token
## 설치 & 실행
```bash
pip install -r requirements.txt
Selenium 기반 `/checkvote` 사용 시 Chrome + `webdriver-manager` 설치 필요.
## 주요 명령어
| 분류 | 예시 |
|------|------|
## 프로젝트 구조
## 개발 가이드 (새 명령 추가)
## 문제 해결
## 최근 변경
## 지원
## 라이선스
내부/팀 사용. 재배포 시 팀 명시 권장.
# HiRest Secure Bot

HiRest 마인크래프트 서버 종합 관리 Discord 봇

## 🚀 주요 기능

### 플레이어 관리
- 차단/임시차단/차단해제
- 킥/뮤트/뮤트해제
- 플레이어 정보 조회
- 온라인 플레이어 목록 조회

### 플레이어 설정
- 권한 등급 설정
- 닉네임 변경
- 추천 보상 지급
- **추천 정보 조회** (NEW!)

### 로그 관리
- 차단 로그 검색
- 차단 로그 업로드
- 중복 로그 제거
- 로그 삭제

## 📦 설치 및 실행

### 1. 환경 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
DISCORD_TOKEN=your_discord_bot_token
TARGET_GUILD_ID=your_guild_id
API_REQUEST_CHANNEL_ID=api_channel_id
ILUNAR_CONSOLE_CHANNEL_ID=console_channel_id
BAN_LOG_CHANNEL_ID=ban_log_channel_id
LOG_CHANNEL_ID=log_channel_id
STAFF_ROLE_ID=staff_role_id
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

**필수 패키지:**
- `py-cord` - Discord 봇 라이브러리
- `python-dotenv` - 환경 변수 관리
- `selenium` - 웹 스크래핑 (checkvote 명령어용)
- `beautifulsoup4` - HTML 파싱 (checkvote 명령어용)
- `webdriver-manager` - Chrome WebDriver 자동 관리

### 3. Chrome WebDriver 설정

`/checkvote` 명령어를 사용하려면 Chrome과 WebDriver가 필요합니다.

#### Windows
```bash
pip install webdriver-manager
```

#### Linux (Ubuntu/Debian)
```bash
# Chrome 설치
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# WebDriver 자동 관리
pip install webdriver-manager
```

### 4. 봇 실행

```bash
python main.py
```

## 📖 명령어 사용법

전체 명령어 목록은 [COMMANDS.md](COMMANDS.md)를 참조하세요.

### 추천 정보 조회 (NEW!)

```
/checkvote <vote_id> [server_id]
```

**설명**: 마인리스트 추천 고유번호로 추천 정보를 조회합니다.

**매개변수**:
- `vote_id`: 조회할 추천 고유번호 (필수)
- `server_id`: 서버 ID (선택, 기본값: 16262-ilunar.kr)

**조회 정보**:
- 추천 고유번호
- 게임 아이디
- 추천 시간
- 추천한 서버

**사용 예시**:
```
/checkvote 12345
/checkvote 12345 16262-ilunar.kr
```

**작동 원리**:
1. Selenium을 사용하여 마인리스트 웹 페이지에 접속
2. BeautifulSoup으로 HTML 파싱
3. 추천 정보 추출 및 Discord 임베드로 표시

## 🏗️ 프로젝트 구조

```
secure/
├── main.py              # 봇 메인 파일
├── requirements.txt     # 패키지 목록
├── README.md           # 이 파일
├── COMMANDS.md         # 명령어 가이드
├── commands/           # 명령어 모듈
│   ├── ban.py
│   ├── tempban.py
│   ├── unban.py
│   ├── mute.py
│   ├── unmute.py
│   ├── vote.py
│   ├── checkvote.py   # NEW!
│   └── ...
├── core/              # 핵심 기능
│   ├── base.py
│   ├── command_bridge.py
│   └── config.py
├── uncommands/        # 권한 체크 안 하는 명령어
│   ├── help.py
│   └── ...
└── utils/             # 유틸리티
    ├── constants.py
    ├── decorators.py
    └── utils.py
```

## 🔧 개발 가이드

### 새 명령어 추가하기

1. `commands/` 폴더에 새 Python 파일 생성
2. 다음 구조로 명령어 작성:

```python
"""명령어 설명."""

import discord
from discord.ext import commands
from utils.utils import create_embed, CommandLogger
from utils.decorators import check_staff_permission

async def handle_command(ctx: discord.ApplicationContext, ...):
    """명령어 처리 로직."""
    # 권한 체크
    if not await check_staff_permission(ctx):
        return
    
    # 명령어 로직 구현
    ...

async def setup(bot: commands.Bot):
    """명령어 등록."""
    @bot.slash_command(name="mycommand", description="설명")
    async def my_command(ctx: discord.ApplicationContext, ...):
        await handle_command(ctx, ...)
```

3. 봇이 자동으로 로드합니다 (재시작 필요)

## 🐛 문제 해결

### Chrome WebDriver 오류
```
오류: Chrome WebDriver가 설치되어 있는지 확인해주세요.
```

**해결 방법**:
```bash
pip install --upgrade webdriver-manager selenium
```

### 권한 오류
```
❌ 권한 부족: 이 명령어를 사용할 권한이 없습니다.
```

**해결 방법**:
- `.env` 파일의 `STAFF_ROLE_ID`가 올바른지 확인
- Discord에서 스태프 역할이 부여되었는지 확인

### 명령어가 표시되지 않음

**해결 방법**:
1. 봇 재시작
2. Discord에서 슬래시 명령어 캐시 삭제:
   - 설정 → 고급 → 개발자 모드 활성화
   - 서버 우클릭 → 서버 나가기 → 다시 입장

## 📝 변경 사항

### v2.1 (Latest)
- ✨ **NEW**: `/checkvote` 명령어 추가 - 마인리스트 추천 정보 조회
- 📦 Selenium 및 BeautifulSoup 패키지 추가
- 📖 COMMANDS.md 및 help 명령어 업데이트

### v2.0
- 🎉 전체 코드베이스 리팩토링
- 📁 모듈화된 명령어 구조
- 🔐 향상된 권한 시스템
- 📊 개선된 로깅 시스템

## 📞 지원

- GitHub Issues: [문제 보고](https://github.com/stack1245/HiRest-Secure/issues)
- Discord: [HiRest 서버](https://discord.gg/hrst)

## 📄 라이선스

Copyright © HiRest Team. All rights reserved.

---

Made with ❤️ by HiRest Team
