from typing import Optional
from mcipc.rcon.je import Client

from .errors import RconErr, CommErr
from .constants import MINECRAFT_COMMS
from .protocol import ServerRcon


class McipcRcon(ServerRcon):
    def __init__(
        self,
        port: int,
        pwd: Optional[str],
        timeout: float,
        max_comm_len: int,
        banned_comms: list[str],
    ) -> None:
        if port < 0 or port > 65535:
            raise ValueError("Rcon port outside valid range")

        if timeout <= 0:
            raise ValueError("Rcon timeout must be greater than zero")

        if max_comm_len <= 0:
            raise ValueError("Maximum command length must be greater than zero")

        for comm in banned_comms:
            if comm not in MINECRAFT_COMMS:
                raise ValueError(
                    f"Invalid minecraft command provided on banned commands: {comm}"
                )

        self._port: int = port
        self._pwd: Optional[str] = pwd
        self._timeout: float = timeout
        self._max_comm_len: int = max_comm_len
        self._bcomms: list[str] = banned_comms

        self._bcomms.extend(ServerRcon.ILLEGAL_COMMS)

    def execute(self, comm: str) -> str:
        if not comm.strip():
            raise CommErr("The command is empty")

        if len(comm) > self._max_comm_len:
            raise CommErr("The command is too long")

        for icomm in McipcRcon.ILLEGAL_COMMS:
            if icomm in comm.lower():
                raise CommErr(f"Command {icomm} is not allowed")
        try:
            with Client(
                ServerRcon.HOST, self._port, passwd=self._pwd, timeout=self._timeout
            ) as client:
                return client.run(comm)
        except Exception as e:
            raise RconErr(str(e))
