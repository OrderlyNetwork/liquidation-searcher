from abc import ABC, abstractmethod
from enum import Enum


class Collector(ABC):
    @abstractmethod
    def start(self, timeout):
        pass

    @abstractmethod
    async def get_event_stream(self):
        pass


class Strategy(ABC):
    @abstractmethod
    async def sync_state(self):
        pass

    @abstractmethod
    async def process_event(self, event):
        pass


class Executor(ABC):
    @abstractmethod
    async def sync_state(self):
        pass

    @abstractmethod
    async def execute(self, action):
        pass


class EventType(str, Enum):
    ORDERLY_LIQUIDATION_REST = "orderly_liquidation_rest"
    ORDERLY_LIQUIDATION_WS = "orderly_liquidation_ws"
    ORDERLY_EXECUTOR_RESULT = "orderly_executor_result"


class ActionType(str, Enum):
    ORDERLY_LIQUIDATION_ORDER = "orderly_liquidation_order"


class LiquidationType(str, Enum):
    LIQUIDATED = "liquidated"
    CLAIM = "claim"
