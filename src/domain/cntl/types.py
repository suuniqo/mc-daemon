from enum import Enum


class ServerStatus(Enum):
    CLOSED  = "CLOSED"
    OPEN    = "OPEN"
    OPENING = "OPENING"
    CLOSING = "CLOSING"
