from abc import abstractmethod
from typing import Protocol

from conf.types import GlobalConf


class GlobalConfLoader(Protocol):
    """
    Factory class for `ServerConf`
    """

    @abstractmethod
    def load(self) -> GlobalConf:
        """
        Factory method that creates a new instance of `ServerConf`
        Raises `ConfLoaderErr` if anything goes wrong
        """
        ...
