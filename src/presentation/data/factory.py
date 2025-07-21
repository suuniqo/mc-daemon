
from conf.types import ServerConf

from domain.event.ebus import ServerEventBus

from domain.mntr.factory import MntrFactory
from domain.cntl.factory import CntlFactory

from services.conn.psutil_conn import PsutilConn
from services.rcon.mcipc_rcon import McipcRcon

from .types import BotData


class BotDataFactory:
    @staticmethod
    def make(conf: ServerConf, ebus: ServerEventBus) -> BotData:
        conn = PsutilConn(conf.minecraft_port)
        rcon = McipcRcon(
            port=conf.rcon_port,
            timeout=conf.rcon_timeout,
            pwd=conf.rcon_pwd,
            max_comm_len=conf.rcon_max_comm_len,
            banned_comms=conf.rcon_banned_comm,
        )

        return BotData(
            conn=conn,
            rcon=rcon,
            mntr=MntrFactory.make(conf, conn, ebus),
            cntl=CntlFactory.make(conf, conn, ebus),
        )
