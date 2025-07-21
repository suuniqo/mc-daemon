import logging

from typing import Callable

from services.wait.poller import Poller

from .types import ServerEvent

class ServerEventBus:
    """
    Allows communication between classes through events
    """

    def __init__(self) -> None:
        self._handlers: dict[ServerEvent, list[Callable[[], None]]] = {}
        self._handling: set[ServerEvent] = set()
        self._logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def subscribe(self, event: ServerEvent, handler: Callable[[], None]) -> None:
        """
        The caller suscribes to an event so that when it is emitted,
        the provided handler is called
        """
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event: ServerEvent) -> None:
        """
        After emitting an event all the subscribed handlers are called
        """
        #TODO: remove this stuff too
        #Raises `EventErr` in case of an event being emitted concurrently
        #if not event in self._handlers:
            #return
        #if event in self._handling:
            #raise EventErr(f"Event {event} was emitted concurrently")

        for handler in self._handlers[event]:
            try:
                # TODO: remove this stuff
                #if asyncio.iscoroutinefunction(handler):
                    #await handler()
                #else:
                handler()
            except Exception as e:
                self._logger.error(f"Handler {handler} for event {event} failed: {e}")

        self._handling.remove(event)

    async def wait(self, event: ServerEvent) -> None:
        """
        Sleeps using exponential backoff until the event provided has been handled
        """
        await Poller.wait(lambda: not event in self._handling)
