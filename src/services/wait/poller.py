import asyncio
import random

from typing import Callable, Optional

from .errors import TimeoutExpired


class Poller:
    IMM_RETRIES: int = 8
    MIN_BACKOFF: float = 0.1
    MAX_BACKOFF: float = 1.6
    JITTER_RATIO: float = 0.25

    @staticmethod
    async def wait(supplier: Callable[[], bool], timeout: Optional[float] = None) -> None:
        """
        Sleeps using exponential backoff until the boolean supplier returns true
        Raises `TimeoutExpired` if a timeout is provided and it expires
        """
        backoff = Poller.MIN_BACKOFF
        jitter  = backoff * Poller.JITTER_RATIO

        for _ in range(Poller.IMM_RETRIES):
            if supplier():
                return

            time = backoff + random.uniform(-jitter, jitter)

            await asyncio.sleep(time)

            if timeout:
                timeout -= time

                if timeout <= 0:
                    raise TimeoutExpired


        while not supplier():
            backoff = min(backoff * 2, Poller.MAX_BACKOFF)
            jitter  = backoff * Poller.JITTER_RATIO

            time = backoff + random.uniform(-jitter, jitter)

            await asyncio.sleep(time)

            if timeout:
                timeout -= time

                if timeout <= 0:
                    raise TimeoutExpired
