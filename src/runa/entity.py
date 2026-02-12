from abc import ABC, abstractmethod


class Entity[State](ABC):
    @abstractmethod
    def __getstate__(self) -> State: ...

    @abstractmethod
    def __setstate__(self, state: State) -> None: ...
