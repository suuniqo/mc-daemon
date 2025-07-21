import logging

from typing import Callable

from .types import ServerEvent

class ServerEventBus:
    """
    Allows communication between classes through events
    """
    def __init__(self) -> None:
        self._handlers: dict[ServerEvent, list[Callable[[], None]]] = {}
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
        for handler in self._handlers[event]:
            try:
                handler()
            except Exception as e:
                self._logger.error(f"Handler {handler} for event {event} failed: {e}")
