import asyncio
from typing import Set

from orderly_sdk.rest import AsyncClient

from liquidation_searcher.types import Collector, EventType
from liquidation_searcher.utils.event_loop import get_loop
from liquidation_searcher.utils.log import logger


class OrderlyLiquidationRestCollector(Collector):
    pushed_liquidations: Set[int]

    def __init__(self, account_id, endpoint, loop=None):
        self.orderly_rest_client = AsyncClient(
            account_id=account_id,
            endpoint=endpoint,
        )
        self.queue = asyncio.Queue(maxsize=512)
        self.loop = loop or get_loop()
        self.pushed_liquidations = set()

    async def _run(self):
        while True:
            res = await self.orderly_rest_client.get_liquidation(params=None)
            logger.debug("orderly liquidation rest collector: {}", res)
            for liquidation in res["data"]["rows"]:
                liquidation_id = liquidation["liquidation_id"]
                if liquidation_id not in self.pushed_liquidations:
                    self.pushed_liquidations.add(liquidation_id)
                    liquidation["event_type"] = EventType.ORDERLY_LIQUIDATION_REST
                    await self.queue.put(liquidation)
            await asyncio.sleep(2)

    def start(self, timeout=None):
        self.loop.call_soon_threadsafe(asyncio.create_task, self._run())

    async def get_event_stream(self):
        if not self.queue.empty():
            return await self.queue.get()
        else:
            return
