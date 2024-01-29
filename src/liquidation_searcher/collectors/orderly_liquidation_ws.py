import asyncio

from orderly_sdk.ws import OrderlyPublicWsManager

from liquidation_searcher.types import Collector, EventType
from liquidation_searcher.utils.event_loop import get_loop
from liquidation_searcher.utils.log import logger


class OrderlyLiquidationWsCollector(Collector):
    def __init__(self, account_id, endpoint, loop=None):
        self.orderly_ws_client = OrderlyPublicWsManager(
            account_id=account_id,
            endpoint=endpoint,
        )
        self.orderly_ws_client.subscribe("liquidation")
        self.queue = asyncio.Queue(maxsize=512)
        self.loop = loop or get_loop()

    async def _run(self, timeout):
        self.orderly_ws_client.start(timeout=15)
        while True:
            res = await self.orderly_ws_client.recv("liquidation", timeout=timeout)
            logger.debug("orderly liquidation ws collector: {}", res)
            for liquidation in res:
                liquidation["event_type"] = EventType.ORDERLY_LIQUIDATION_WS
                await self.queue.put(liquidation)

    def start(self, timeout=30):
        self.loop.call_soon_threadsafe(asyncio.create_task, self._run(timeout))

    async def get_event_stream(self):
        if not self.queue.empty():
            await self.queue.get()
        else:
            return
