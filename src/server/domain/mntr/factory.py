from conf.types import GlobalConf

from server.services.conn.protocol import ServerConn
from server.domain.event.ebus import ServerEventBus

from .protocol import ServerMntr
from .event_mntr import EventMntr


class MntrFactory:
    @staticmethod
    def make(conf: GlobalConf, conn: ServerConn, ebus: ServerEventBus) -> ServerMntr:
        """
        Makes a new instance of `ServerMntr` through `ServerConf`
        """
        return EventMntr(
            idle_timeout=conf.idle_timeout,
            polling_intv=conf.polling_intv,
            conn=conn,
            ebus=ebus,
        )
