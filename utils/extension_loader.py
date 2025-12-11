"""확장 로더"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List

from discord.ext import commands


class ExtensionLoader:
    """명령어 확장 동적 로드"""
    
    def __init__(self, bot: commands.Bot, module_name: str = "Bot"):
        self.bot = bot
        self.module_name = module_name
        self.loaded_extensions: List[str] = []
        self.failed_extensions: Dict[str, str] = {}

    def load_all_extensions(self, commands_dir: str = "commands") -> None:
        """모든 확장 로드"""
        base_path = Path(__file__).parent.parent
        commands_path = base_path / commands_dir
        if not commands_path.exists():
            return
        extension_files = self._discover_extensions(commands_path, commands_dir)
        if not extension_files:
            return
        for extension in extension_files:
            self.load_extension(extension)
    
    def _discover_extensions(self, commands_path: Path, commands_dir: str) -> List[str]:
        """확장 파일 검색"""
        extension_files = []
        group_folders = set()
        
        for folder_path in commands_path.rglob('*'):
            if folder_path.is_dir() and self._is_valid_extension_directory(folder_path):
                if self._has_init_file(folder_path):
                    group_folders.add(folder_path)
                    relative_path = folder_path.relative_to(commands_path.parent)
                    extension_name = str(relative_path).replace(os.sep, '.')
                    extension_files.append(extension_name)
        
        for file_path in commands_path.rglob('*.py'):
            if self._is_valid_extension_file(file_path):
                is_in_group = any(file_path.is_relative_to(gf) for gf in group_folders)
                if not is_in_group:
                    relative_path = file_path.relative_to(commands_path.parent)
                    extension_name = str(relative_path.with_suffix('')).replace(os.sep, '.')
                    extension_files.append(extension_name)
        
        return sorted(extension_files)
    
    def _is_valid_extension_file(self, file_path: Path) -> bool:
        """유효 파일 확인"""
        return (not file_path.name.startswith('__') and 
                not file_path.name.startswith('.') and
                file_path.suffix == '.py')
    
    def _is_valid_extension_directory(self, dir_path: Path) -> bool:
        """유효 디렉토리 확인"""
        invalid_names = {'__pycache__', '.git'}
        return (not dir_path.name.startswith('__') and 
                not dir_path.name.startswith('.') and
                dir_path.name not in invalid_names)
    
    def _has_init_file(self, dir_path: Path) -> bool:
        """__init__.py 파일 확인"""
        return (dir_path / '__init__.py').exists()
    
    def _get_group_files(self, extension_name: str) -> list[str]:
        """그룹 파일 목록 가져오기"""
        base_path = Path(__file__).parent.parent
        folder_path = base_path / extension_name.replace('.', os.sep)
        
        if not folder_path.exists():
            return []
        
        files = []
        for file_path in sorted(folder_path.glob('*.py')):
            if self._is_valid_extension_file(file_path):
                files.append(file_path.stem)
        
        return files
    
    def load_extension(self, extension_name: str) -> tuple[bool, int]:
        """확장 로드"""
        try:
            self.bot.load_extension(extension_name)
            self.loaded_extensions.append(extension_name)
            files = self._get_group_files(extension_name)
            return True, len(files) if files else 1
        except Exception as e:
            self.failed_extensions[extension_name] = str(e)
            files = self._get_group_files(extension_name)
            return False, len(files) if files else 1
    
    def _get_display_name(self, extension_name: str) -> str:
        """확장 표시명 생성"""
        return extension_name.replace('commands.', '').replace('.', '/')
    
    def reload_extension(self, extension_name: str) -> bool:
        """확장 재로드."""
        try:
            self.bot.reload_extension(extension_name)
            return True
        except Exception:
            return False

    def unload_extension(self, extension_name: str) -> bool:
        """확장 언로드."""
        try:
            self.bot.unload_extension(extension_name)
            if extension_name in self.loaded_extensions:
                self.loaded_extensions.remove(extension_name)
            return True
        except Exception:
            return False
    
    def reload_all_extensions(self) -> None:
        """모든 확장 재로드."""
        success_count = 0
        for extension in self.loaded_extensions.copy():
            if self.reload_extension(extension):
                success_count += 1

    def load_specific_extension(self, extension_path: str) -> bool:
        """특정 경로의 확장 로드."""
        ok, _ = self.load_extension(extension_path)
        return ok
    
    def get_loaded_extensions(self) -> List[str]:
        """로드된 확장 목록 반환."""
        return self.loaded_extensions.copy()
    
    def get_failed_extensions(self) -> Dict[str, str]:
        """실패한 확장 목록 반환."""
        return self.failed_extensions.copy()
    
    def get_extension_status(self) -> Dict[str, Any]:
        """확장 로드 상태 정보 반환."""
        return {
            'loaded_count': len(self.loaded_extensions),
            'failed_count': len(self.failed_extensions),
            'loaded_extensions': self.get_loaded_extensions(),
            'failed_extensions': self.get_failed_extensions()
        }
    
