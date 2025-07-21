from dataclasses import dataclass

from domain.cntl.protocol import ServerCntl
from domain.mntr.protocol import ServerMntr

from services.conn.protocol import ServerConn
from services.rcon.protocol import ServerRcon


@dataclass
class ServerData:
    conn: ServerConn
    rcon: ServerRcon
    mntr: ServerMntr
    cntl: ServerCntl
