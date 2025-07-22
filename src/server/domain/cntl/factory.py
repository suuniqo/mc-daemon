from conf.types import GlobalConf

from server.services.conn.protocol import ServerConn
from server.services.proc.minecraft_proc import MinecraftProc

from server.domain.event.ebus import ServerEventBus

from .protocol import ServerCntl
from .event_cntl import EventCntl


class CntlFactory:
    @staticmethod
    def make(conf: GlobalConf, conn: ServerConn, ebus: ServerEventBus) -> ServerCntl:
        """
        Makes a new instance of `ServerCntl` through `ServerConf`
        """
        return EventCntl(
            conn=conn,
            proc=MinecraftProc(conf.process_script, conf.process_timeout),
            ebus=ebus,
            startup_timeout=conf.startup_timeout,
        )
