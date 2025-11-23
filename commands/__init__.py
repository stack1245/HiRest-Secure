"""명령어 패키지.

각 명령어는 setup() 함수를 통해 동적으로 로드됩니다.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _discover_commands():
    """명령어 파일 검색."""
    commands_dir = Path(__file__).parent
    command_modules = []
    
    for file_path in commands_dir.glob("*.py"):
        if file_path.name.startswith("_") or file_path.name == "__init__.py":
            continue
        
        module_name = file_path.stem
        command_modules.append(module_name)
    
    return sorted(command_modules)


__all__ = _discover_commands()

logger.debug(f"발견된 명령어: {__all__}")