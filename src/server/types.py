from dataclasses import dataclass

from server.domain.cntl.protocol import ServerCntl
from server.domain.mntr.protocol import ServerMntr

from server.services.conn.protocol import ServerConn
from server.services.rcon.protocol import ServerRcon


@dataclass
class ServerData:
    conn: ServerConn
    rcon: ServerRcon
    mntr: ServerMntr
    cntl: ServerCntl
