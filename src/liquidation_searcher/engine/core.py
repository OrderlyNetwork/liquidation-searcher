import asyncio
from typing import List

from liquidation_searcher.types import Collector, Executor, Strategy
from liquidation_searcher.utils.log import logger


class Engine:
    collectors: List[Collector]
    strategies: List[Strategy]
    executors: List[Executor]
    tasks: List[asyncio.Task]
    event_channel_capacity: int
    action_channel_capacity: int
    event_queue: asyncio.Queue
    action_queue: asyncio.Queue

    def __init__(
        self,
        event_channel_capacity: int = 512,
        action_channel_capacity: int = 512,
    ):
        self.collectors = []
        self.strategies = []
        self.executors = []
        self.tasks = []
        self.event_channel_capacity = event_channel_capacity
        self.action_channel_capacity = action_channel_capacity
        self.event_queue = asyncio.Queue(self.event_channel_capacity)
        self.action_queue = asyncio.Queue(self.action_channel_capacity)

    def add_collector(self, collector: Collector):
        self.collectors.append(collector)

    def add_strategy(self, strategy: Strategy):
        self.strategies.append(strategy)

    def add_executor(self, executor: Executor):
        self.executors.append(executor)

    async def run_collectors(self):
        for collector in self.collectors:
            collector.start(timeout=30)
        while True:
            for collector in self.collectors:
                event = await collector.get_event_stream()
                if event is not None:
                    logger.debug("engine collector event: {}", event)
                    await self.event_queue.put(event)
            await asyncio.sleep(0.1)

    async def run_strategies(self):
        for strategy in self.strategies:
            await strategy.sync_state()
        while True:
            if not self.event_queue.empty():
                event = await self.event_queue.get()
                if event is not None:
                    logger.debug("engine strategy event: {}", event)

                    async def process_event(strategy, event):
                        action = await strategy.process_event(event)
                        await self.action_queue.put(action)

                    tasks = []
                    for strategy in self.strategies:
                        tasks.append(
                            asyncio.create_task(process_event(strategy, event))
                        )
                    await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

    async def run_executors(self):
        for executor in self.executors:
            await executor.sync_state()
        while True:
            if not self.action_queue.empty():
                action = await self.action_queue.get()
                if action is not None:
                    logger.debug("engine executor action: {}", action)

                    async def execute(executor, action):
                        await executor.execute(action)

                    tasks = []
                    for executor in self.executors:
                        tasks.append(asyncio.create_task(execute(executor, action)))
                    await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

    async def run(self):
        self.tasks = []
        self.tasks.append(asyncio.create_task(self.run_executors()))
        self.tasks.append(asyncio.create_task(self.run_strategies()))
        self.tasks.append(asyncio.create_task(self.run_collectors()))
        await asyncio.gather(*self.tasks)
