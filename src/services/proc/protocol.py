from abc import abstractmethod
from typing import Protocol


class ServerProc(Protocol):
    """
    Abstracts the logic and error handling behind managing the server process
    """

    @abstractmethod
    def start(self) -> None:
        """
        Starts the process
        Raises `ProcErr` if the process hadn't stopped or if it can't be started
        """
        ...

    @abstractmethod
    def alive(self) -> bool:
        """
        The process won't be alive if it hasn't started yet or if it has crashed
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the process
        Raises `ProcErr` if the process hadn't started or if it can't be stopped
        """
        ...

    @abstractmethod
    def kill(self) -> None:
        """
        Kills the process
        """
        ...
