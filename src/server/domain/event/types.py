from enum import Enum


class ServerEvent(Enum):
    OPENED   = "OPENED"         # server has finished startup
    CLOSED   = "CLOSED"         # server has finished closing
    OPENING  = "OPENING"        # server is opening
    CLOSING  = "CLOSING"        # server is closing
    CRASHED  = "CRASHED"        # serves has crashed
    HUNG     = "HUNG"           # server timed out during startup
    OCCUPIED = "OCCUPIED"       # server has been occupied after being empty
    EMPTY    = "EMPTY"          # server is empty after being occupied
    IDLE     = "IDLE"           # server idle timeout has expired
