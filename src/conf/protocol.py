from abc import abstractmethod
from typing import Protocol

from .types import ServerConf


class ServerConfLoader(Protocol):
    """
    Factory class for `ServerConf`
    """

    @abstractmethod
    def load(self) -> ServerConf:
        """
        Factory method that creates a new instance of `ServerConf`
        Raises `ServerConfLoaderErr` if anything goes wrong
        """
        ...
