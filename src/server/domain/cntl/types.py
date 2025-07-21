from enum import Enum


class ServerStatus(Enum):
    CLOSED  = "CLOSED"
    OPEN    = "OPEN"
    OPENING = "OPENING"
    CLOSING = "CLOSING"

    def __str__(self) -> str:
        return str(self).lower()
