from abc import abstractmethod
from typing import Protocol


class BotLogger(Protocol):
    """
    Logs events through a channel specified by the user
    """
    @abstractmethod
    def start(self) -> None:
        """
        Starts the logging task
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the logging task
        """
        ...
