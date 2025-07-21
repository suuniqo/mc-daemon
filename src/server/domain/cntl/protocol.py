from abc import abstractmethod
from typing import Protocol

from .types import ServerStatus


class ServerCntl(Protocol):
    """
    Manages the server status and provides methods to control it
    """

    @abstractmethod
    def status(self) -> ServerStatus:
        """
        Returns the current status of the server
        """
        ...

    @abstractmethod
    def try_open(self) -> bool:
        """
        Tries to open the server, returns wether it has opened or not
        """
        ...

    @abstractmethod
    def try_close(self) -> bool:
        """
        Tries to close the server, returns wether it has closed or not
        """
        ...

    @abstractmethod
    def try_restart(self) -> bool:
        """
        Tries to restart the server, returns wether it has restarted or not
        """
        ...

    @abstractmethod
    async def wait_open(self) -> bool:
        """
        Sleeps until the server opens or the timeout expires
        Returns wether it opened or not
        """
        ...
