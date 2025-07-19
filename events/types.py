from enum import Enum
from typing import Callable, Awaitable

class ServerEvent(Enum):
    OPENING  = "OPENING"
    OPENED   = "OPENED"
    CLOSING  = "CLOSING"
    CLOSED   = "CLOSED"
    CRASHED  = "CRASHED"
    OCCUPIED = "OCCUPIED"
    EMPTY    = "EMPTY"
    TIMEOUT  = "TIMEOUT"

type Handler = Callable[[], None] | Callable[[], Awaitable[None]]
