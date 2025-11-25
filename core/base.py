"""Core base classes and utilities."""
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar('T')


@dataclass(frozen=True)
class CommandResult(Generic[T]):
    """명령어 실행 결과를 담는 불변 데이터 클래스."""
    
    success: bool
    data: Optional[T] = None
    error_message: Optional[str] = None

    @classmethod
    def success_with(cls, data: T) -> 'CommandResult[T]':
        return cls(success=True, data=data)

    @classmethod
    def success(cls) -> 'CommandResult[None]':
        return cls(success=True)

    @classmethod
    def failure(cls, error_message: str) -> 'CommandResult[T]':
        return cls(success=False, error_message=error_message)

    def __bool__(self) -> bool:
        return self.success


class Singleton(type):
    """싱글톤 패턴 구현을 위한 메타클래스."""
    
    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
