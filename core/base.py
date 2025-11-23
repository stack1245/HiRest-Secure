from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar('T')


@dataclass(frozen=True)
class CommandResult(Generic[T]):

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
    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
