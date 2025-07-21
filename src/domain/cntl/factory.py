from conf.types import ServerConf
from services.proc.minecraft_proc import MinecraftProc
from services.conn.psutil_conn import PsutilConn

from cntl.event_cntl import EventCntl
from cntl.protocol import ServerCntl
from event.ebus import ServerEventBus


class CntlFactory:
    @staticmethod
    def make(conf: ServerConf, ebus: ServerEventBus) -> ServerCntl:
        """
        Makes a new instance of `ServerCntl` through `ServerConf`
        """
        return EventCntl(
            conn=PsutilConn(conf.minecraft_port),
            proc=MinecraftProc(conf.process_script, conf.process_timeout),
            ebus=ebus,
            startup_timeout=conf.startup_timeout,
        )
