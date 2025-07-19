from typing import Optional
from mcipc.rcon.je import Client

from .protocol import ServerRcon
from .errors import RconErr, CommErr


class McipcServerRcon(ServerRcon):
    def __init__(
        self,
        port: int,
        pwd: Optional[str],
        timeout: Optional[int],
        max_comm_len: int,
        banned_comms: list[str],
    ) -> None:
        self._port: int = port
        self._pwd: Optional[str] = pwd
        self._timeout: Optional[int] = timeout
        self._max_comm_len: int = max_comm_len
        self._bcomms: list[str] = banned_comms

        self._bcomms.extend(ServerRcon.ILLEGAL_COMMS)

    def execute(self, comm: str) -> str:
        if not comm.strip() or len(comm) > self._max_comm_len:
            raise CommErr("Invalid command format")

        for icomm in McipcServerRcon.ILLEGAL_COMMS:
            if icomm in comm.lower():
                raise CommErr(f"Command {icomm} is not allowed")
        try:
            with Client(
                ServerRcon.HOST, self._port, passwd=self._pwd, timeout=self._timeout
            ) as client:
                return client.run(comm)
        except Exception as e:
            raise RconErr(str(e))
