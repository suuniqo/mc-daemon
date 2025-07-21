import asyncio
import logging

from services.conn.protocol import ServerConn
from services.conn.errors import TimeoutExpired

from services.proc.protocol import ServerProc
from services.proc.errors import ProcErr

from event.ebus import ServerEventBus
from event.types import ServerEvent

from .types import ServerStatus
from .protocol import ServerCntl


class EventCntl(ServerCntl):
    def __init__(
        self,
        conn: ServerConn,
        proc: ServerProc,
        ebus: ServerEventBus,
        startup_timeout: float,
    ) -> None:
        if startup_timeout <= 0:
            raise ValueError("Startup timeout must be greater than zero")

        self._status: ServerStatus = ServerStatus.CLOSED
        self._logger: logging.Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

        self._conn: ServerConn = conn
        self._proc: ServerProc = proc
        self._ebus: ServerEventBus = ebus
        self._startup_timeout: float = startup_timeout

        self._ebus.subscribe(ServerEvent.IDLE, lambda: (self.try_close(), None)[1])
        self._ebus.subscribe(ServerEvent.CRASHED, lambda: (self.try_restart(), None)[1])

    async def _handle_startup(self) -> None:
        """
        Tracks the startup and updates the status if the server finishes opening or it freezes
        Emits event `HUNG` if it freezes and event 'OPENED' if it opens correctly
        """
        if await self.wait_open():
            self._status = ServerStatus.OPEN
            self._ebus.emit(ServerEvent.OPENED)
            return

        self._proc.kill()
        self._status = ServerStatus.CLOSED

        self._ebus.emit(ServerEvent.HUNG)

    def status(self) -> ServerStatus:
        return self._status

    def try_open(self) -> bool:
        """
        Tries to open the server, returns wether it has opened or not
        Emits event 'OPENING' when starting the operation
        """
        if self._status != ServerStatus.CLOSED:
            return False

        self._status = ServerStatus.OPENING

        self._ebus.emit(ServerEvent.OPENING)

        try:
            self._proc.start()
            asyncio.create_task(self._handle_startup())
            return True
        except ProcErr as e:
            self._logger.error(f"Server couldn't be opened: {e}")
            self._status = ServerStatus.CLOSED
            return False

    def try_close(self) -> bool:
        """
        Tries to close the server, returns wether it has closed or not
        Emits event 'CLOSING' when starting the operation and event 'CLOSED' when finished closing
        """
        if self._status != ServerStatus.OPEN:
            return False

        self._status = ServerStatus.CLOSING

        self._ebus.emit(ServerEvent.CLOSING)

        try:
            self._proc.stop()
        except ProcErr as e:
            # Nothing can be done, the app assumes the process stopped
            # and the admin needs to manually check if the process is still alive or in a zombie state
            self._logger.error(f"Error closing the server: {e}")

        self._status = ServerStatus.CLOSED

        self._ebus.emit(ServerEvent.CLOSED)

        return True

    def try_restart(self) -> bool:
        return self.try_close() and self.try_open()

    async def wait_open(self) -> bool:
        try:
            await self._conn.wait_open(self._startup_timeout)
            return True
        except TimeoutExpired:
            self._logger.warning("Timeout reached opening the server")
            return False
