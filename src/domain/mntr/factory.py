from conf.types import ServerConf

from services.conn.protocol import ServerConn

from event.ebus import ServerEventBus

from .protocol import ServerMntr
from .event_mntr import EventMntr


class CntlFactory:
    @staticmethod
    def make(conf: ServerConf, conn: ServerConn, ebus: ServerEventBus) -> ServerMntr:
        """
        Makes a new instance of `ServerMntr` through `ServerConf`
        """
        return EventMntr(
            idle_timeout=conf.idle_timeout,
            polling_intv=conf.polling_intv,
            conn=conn,
            ebus=ebus,
        )
