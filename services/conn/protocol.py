from typing import Protocol
from abc import abstractmethod

class ServerConn(Protocol):
    _port: int

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
