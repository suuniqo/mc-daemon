from conf.types import ServerConf

from services.conn.protocol import ServerConn
from services.proc.minecraft_proc import MinecraftProc

from event.ebus import ServerEventBus

from .protocol import ServerCntl
from .event_cntl import EventCntl


class CntlFactory:
    @staticmethod
    def make(conf: ServerConf, conn: ServerConn, ebus: ServerEventBus) -> ServerCntl:
        """
        Makes a new instance of `ServerCntl` through `ServerConf`
        """
        return EventCntl(
            conn=conn,
            proc=MinecraftProc(conf.process_script, conf.process_timeout),
            ebus=ebus,
            startup_timeout=conf.startup_timeout,
        )
