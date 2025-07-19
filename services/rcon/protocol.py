from typing import Protocol, Optional
from abc import abstractmethod

class ServerRcon(Protocol):
    HOST = "127.0.0.1"
    ILLEGAL_COMMS = ["/stop"]

    _port: int
    _pwd: Optional[str]
    _timeout: Optional[int]
    _max_comm_len: int
    _bcomms: list[str]

    @abstractmethod
    def execute(self, comm: str) -> str:
        """
        Executes the command provided through the rcon protocol and returns the response
        Raises `CommErr` if the command format is incorrect or it is banned and `RconErr` if the connection fails
        """
        ...
