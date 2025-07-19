import psutil

from .protocol import ServerConn

class PsutilServerConn(ServerConn):
    def __init__(self, port: int) -> None:
        self._port: int = port

    def is_open(self) -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == self._port:
                return True
        return False

    def is_empty(self) -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_ESTABLISHED and conn.laddr.port == self._port:
                return False
        return True

    def client_count(self) -> int:
        clients = 0

        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_ESTABLISHED and conn.laddr.port == self._port:
                clients += 1
                
        return clients
