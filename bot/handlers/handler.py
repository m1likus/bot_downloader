from abc import ABC, abstractmethod
from enum import Enum


class STATUS(Enum):
    STOP = 1
    CONTINUE = 2


class STATE(Enum):
    WAIT_FOR_TOKEN = "WAIT_FOR_TOKEN"
    WAIT_FOR_RESOLUTION = " WAIT_FOR_RESOLUTION"
    WAIT_FOR_AUDIO = "WAIT_FOR_AUDIO"
    WAIT_FOR_START_DOWNLOADING = "WAIT_FOR_START_DOWNLOADING"
    WAIT_FOR_DOWNLOAD = "WAIT_FOR_DOWNLOAD"


class Handler(ABC):
    @abstractmethod
    def can_handle(self, update: dict, state: STATE) -> bool: ...

    @abstractmethod
    def handle(self, update: dict, state: STATE) -> STATUS: ...
