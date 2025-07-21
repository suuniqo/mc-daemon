from typing import Protocol, Optional
from abc import abstractmethod

class ServerConn(Protocol):
    """
    Provides information about the server looking at the connections on it's port
    """

    @abstractmethod
    def is_open(self) -> bool:
        """
        Checks if the connection on the provided port is open
        """
        ...

    @abstractmethod
    def is_empty(self) -> bool:
        """
        Checks if there are any clients connected to the provided port
        """
        ...

    @abstractmethod
    def client_count(self) -> int:
        """
        Counts the clients connected to the provided port
        """
        ...

    @abstractmethod
    async def wait_open(self, timeout: Optional[float] = None) -> None:
        """
        Sleeps until the connection on the provided port is open or the timeout expires
        Raises `TimeoutExpired` if a timeout is provided and it expires
        """
        ...
