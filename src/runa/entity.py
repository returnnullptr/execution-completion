from abc import ABC, abstractmethod
from typing import Any, Self


class Entity[State](ABC):
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        return super().__new__(cls)

    @abstractmethod
    def __getstate__(self) -> State: ...

    @abstractmethod
    def __setstate__(self, state: State) -> None: ...
