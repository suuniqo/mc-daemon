from typing import Optional

from domain.event.types import ServerEvent
from event.ebus import ServerEventBus

from .protocol import ServerMntr


class EventMntr(ServerMntr):
    def __init__(self, idle_timeout: float, ebus: ServerEventBus) -> None:
        self._idle_since: Optional[float] = None
        self._idle_timeout: float = idle_timeout
        self._ebus: ServerEventBus = ebus

        self._ebus.subscribe(ServerEvent.OPENED, self._start)
        self._ebus.subscribe(ServerEvent.CLOSED, self._stop)

    def _start(self) -> None:
        ...

    def _stop(self) -> None:
        ...

    def _monitor(self) -> None:
        ...
