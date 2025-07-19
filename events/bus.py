import asyncio
import traceback
import logging

from collections import defaultdict
from typing import DefaultDict

from .types import ServerEvent, Handler
from .errors import EventErr

class EventBus:
    IMM_RETRIES: int = 8
    MIN_BAKCOFF: float = 0.1
    MAX_BACKOFF: float = 1.6

    def __init__(self) -> None:
        self._handlers: dict[ServerEvent, list[Handler]] = {}
        self._handling: set[ServerEvent] = set()
        self._locks: DefaultDict[ServerEvent, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def subscribe(self, event: ServerEvent, handler: Handler) -> None:
        """
        The caller suscribes to a server event so that when it is emitted,
        the provided handler is called
        """
        self._handlers.setdefault(event, []).append(handler)

    async def wait(self, event: ServerEvent) -> None:
        """
        Sleeps using exponential backoff until the event provided has been handled
        """
        for _ in range(EventBus.IMM_RETRIES):
            if not event in self._handling:
                return
            await asyncio.sleep(EventBus.MIN_BAKCOFF)

        backoff = EventBus.MIN_BAKCOFF

        while event in self._handling:
            backoff = min(backoff * 2, EventBus.MAX_BACKOFF)
            await asyncio.sleep(backoff)

    
    async def emit(self, event: ServerEvent) -> None:
        """
        After emitting an event all the suscribed handlers are called
        Raises `EventErr` in case of an event being emitted concurrently
        """
        if not event in self._handlers:
            return
        if event in self._handling:
            raise EventErr(f"Event {event} was emitted concurrently")

        for handler in self._handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                self._logger.error(f"Handler {handler} for event {event} failed: {e}")
                traceback.print_exc()

        self._handling.remove(event)
