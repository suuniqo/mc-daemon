from abc import abstractmethod
from typing import Protocol


class ServerProc(Protocol):
    _startup_script: str

    @abstractmethod
    def start(self) -> None:
        """
        Starts the process
        Raises `ServerProcErr` if the process hadn't stopped or if anything goes wrong
        """
        ...

    @abstractmethod
    def alive(self) -> bool:
        """
        The process won't be alive if it hasn't started yet or if it has crashed
        Raises `ServerProcErr` if anything goes wrong
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the process
        Raises `ServerProcErr` if the process hadn't started or if anything goes wrong
        """
        ...
