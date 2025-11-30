from abc import ABC, abstractmethod
from bot.types import STATE, STATUS


class Handler(ABC):
    @abstractmethod
    def can_handle(self, update: dict, state: STATE) -> bool: ...

    @abstractmethod
    async def handle(self, update: dict, state: STATE) -> STATUS: ...
