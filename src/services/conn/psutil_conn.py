import psutil
import random
import asyncio

from typing import Optional

from .protocol import ServerConn
from .errors import TimeoutExpired

class PsutilConn(ServerConn):
    IMM_RETRIES: int = 8
    MIN_BACKOFF: float = 0.1
    MAX_BACKOFF: float = 1.6
    JITTER_RATIO: float = 0.25

    def __init__(self, port: int) -> None:
        self._port: int = port

    def is_open(self) -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == self._port:
                return True
        return False

    def is_empty(self) -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_ESTABLISHED and conn.laddr.port == self._port:
                return False
        return True

    def client_count(self) -> int:
        clients = 0

        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_ESTABLISHED and conn.laddr.port == self._port:
                clients += 1
                
        return clients

    async def wait_open(self, timeout: Optional[float] = None) -> None:
        """
        Sleeps using exponential backoff until the boolean supplier returns true
        Raises `TimeoutExpired` if a timeout is provided and it expires
        """
        backoff = PsutilConn.MIN_BACKOFF
        jitter  = backoff * PsutilConn.JITTER_RATIO

        for _ in range(PsutilConn.IMM_RETRIES):
            if self.is_open():
                return

            time = backoff + random.uniform(-jitter, jitter)

            await asyncio.sleep(time)

            if timeout:
                timeout -= time

                if timeout <= 0:
                    raise TimeoutExpired


        while not self.is_open():
            backoff = min(backoff * 2, PsutilConn.MAX_BACKOFF)
            jitter  = backoff * PsutilConn.JITTER_RATIO

            time = backoff + random.uniform(-jitter, jitter)

            await asyncio.sleep(time)

            if timeout:
                timeout -= time

                if timeout <= 0:
                    raise TimeoutExpired
