from abc import abstractmethod
from typing import Protocol, Optional


class ServerMntr(Protocol):
    """
    Monitors the server while open and performs maintenance
    """
    @abstractmethod
    def timeout_in(self) -> Optional[float]:
        """
        Returns how much time is left until the server shuts down due to inactivity, or None if it is occupied
        """
        ...
