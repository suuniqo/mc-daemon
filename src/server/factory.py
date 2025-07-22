from conf.types import GlobalConf

from server.domain.event.ebus import ServerEventBus
from server.domain.mntr.factory import MntrFactory
from server.domain.cntl.factory import CntlFactory

from server.services.conn.psutil_conn import PsutilConn
from server.services.rcon.mcipc_rcon import McipcRcon

from .types import ServerData


class ServerDataFactory:
    @staticmethod
    def make(conf: GlobalConf, ebus: ServerEventBus) -> ServerData:
        """
        Makes a new instance of `ServerData` through `ServerConf`
        """
        conn = PsutilConn(conf.minecraft_port)
        rcon = McipcRcon(
            port=conf.rcon_port,
            timeout=conf.rcon_timeout,
            pwd=conf.rcon_pwd,
            max_comm_len=conf.rcon_max_comm_len,
            banned_comms=conf.rcon_banned_comm,
        )

        return ServerData(
            conn=conn,
            rcon=rcon,
            mntr=MntrFactory.make(conf, conn, ebus),
            cntl=CntlFactory.make(conf, conn, ebus),
        )
