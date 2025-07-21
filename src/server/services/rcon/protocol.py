from typing import Protocol
from abc import abstractmethod


class ServerRcon(Protocol):
    """
    Abstracts the logic and command parsing behind the minecraft rcon protocol
    """

    HOST = "127.0.0.1"
    ILLEGAL_COMMS = ["/stop"]

    @abstractmethod
    def execute(self, comm: str) -> str:
        """
        Executes the command provided through the rcon protocol and returns the response
        Raises `CommErr` if the command format is incorrect or it is banned and `RconErr` if the connection fails
        """
        ...
