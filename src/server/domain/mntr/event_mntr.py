import asyncio
import logging
import time

from typing import Optional

from server.domain.event.types import ServerEvent
from server.domain.event.ebus import ServerEventBus
from server.services.conn.protocol import ServerConn

from .protocol import ServerMntr


class EventMntr(ServerMntr):
    def __init__(
        self,
        idle_timeout: Optional[float],
        polling_intv: float,
        conn: ServerConn,
        ebus: ServerEventBus,
    ) -> None:
        if idle_timeout is not None and idle_timeout <= 0:
            raise ValueError("Startup timeout must be greater than zero")

        if polling_intv <= 0:
            raise ValueError("Polling interval must be greater than zero")

        self._task: Optional[asyncio.Task] = None
        self._idle_since: Optional[float] = None
        self._logger: logging.Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

        self._idle_timeout: Optional[float] = idle_timeout
        self._polling_intv: float = polling_intv
        self._conn: ServerConn = conn
        self._ebus: ServerEventBus = ebus

        self._ebus.subscribe(ServerEvent.OPENED, self._start)
        self._ebus.subscribe(ServerEvent.CLOSING, self._stop)

    def timeout_in(self) -> Optional[float]:
        if self._idle_timeout is None:
            return None
        if self._idle_since is None:
            return None

        return max(self._idle_timeout - (time.time() - self._idle_since), 0)

    def _start(self) -> None:
        """
        Tries to start the monitor task
        """
        if self._task is not None and not self._task.done():
            self._logger.warning("Tried to start monitor while already running")
            return

        self._task = asyncio.create_task(self._monitor_loop())

    def _stop(self) -> None:
        """
        Tries to stop the monitor task
        """
        if self._task is None or self._task.done():
            self._task = None
            self._logger.warning("Tried to stop monitor while not running yet")
            return

        self._task.cancel()

    def _crash_check(self):
        """
        Checks if the serves has unexpectedly crashed
        Emits `CRASHED` if the server has stopped listening for clients
        """
        if not self._conn.is_open():
            self._ebus.emit(ServerEvent.CRASHED)

    def _empty_check(self):
        """
        Checks if the server is empty and how long has it been like that
        Emits `OCCUPIED` if it has been occupied after just being empty
        Emits `EMPTY` if it has emptied after just being occupied
        Emits `IDLE` if it has been empty longer than the provided timeout
        """
        if self._idle_timeout is None:
            return

        if not self._conn.is_empty():
            if self._idle_since is not None:
                self._ebus.emit(ServerEvent.OCCUPIED)
                self._idle_since = None
            return

        if self._idle_since is None:
            self._idle_since = time.time()
            self._ebus.emit(ServerEvent.EMPTY)
        elif time.time() - self._idle_since > self._idle_timeout:
            self._ebus.emit(ServerEvent.IDLE)

    async def _monitor_loop(self) -> None:
        """
        Continous task that performs various health checks on the server
        """
        try:
            while True:
                self._crash_check()
                self._empty_check()
                await asyncio.sleep(self._polling_intv)
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._idle_since = None
