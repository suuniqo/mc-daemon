import asyncio

from typing import Callable

from .ebus import ServerEventBus
from .types import ServerEvent


class MemoryEventBus(ServerEventBus):
    """
    This class stores all the events (that the user has subscribed to) emitted by the bus
    """
    def __init__(self, subs: list[ServerEvent]) -> None:
        self._queue: asyncio.Queue[ServerEvent] = asyncio.Queue()
        self._subs: list[ServerEvent] = subs
        super().__init__()

    def subscribe(self, event: ServerEvent, handler: Callable[[], None]) -> None:
        return super().subscribe(event, handler)

    def emit(self, event: ServerEvent) -> None:
        if event in self._subs:
            self._queue.put_nowait(event)

        super().emit(event)

    async def pop(self) -> ServerEvent:
        """
        Waits until there is an event in the queue and pops it
        """
        return await self._queue.get()
