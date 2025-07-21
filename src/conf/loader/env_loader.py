import os

from dotenv import load_dotenv
from typing import Callable, Optional, TypeVar

from conf.types import ServerConf

from .errors import ConfLoaderErr
from .protocol import ServerConfLoader


class EnvConfLoader(ServerConfLoader):
    ENV_DISCORD_TOKEN       = "DISCORD_TOKEN"
    ENV_DISCORD_GUILD       = "DISCORD_GUILD"
    ENV_DISCORD_LOG_CHANNEL = "DISCORD_LOG_CHANNEL"
    ENV_PROCESS_SCRIPT      = "PROCESS_SCRIPT"
    ENV_PROCESS_TIMEOUT     = "PROCESS_TIMEOUT"
    ENV_MINECRAFT_PORT      = "MINECRAFT_PORT"
    ENV_RCON_PORT           = "RCON_PORT"
    ENV_RCON_PWD            = "RCON_PWD"
    ENV_RCON_TIMEOUT        = "RCON_TIMEOUT"
    ENV_RCON_MAX_COMM_LEN   = "RCON_MAX_COMM_LEN"
    ENV_RCON_BANNED_COMM    = "RCON_BANNED_COMM"
    ENV_STARTUP_TIMEOUT     = "STARTUP_TIMEOUT"
    ENV_IDLE_TIMEOUT        = "IDLE_TIMEOUT"
    ENV_POLLING_INTV        = "POLLING_INTV"

    T = TypeVar("T")

    @staticmethod
    def _list_from_env(env: str) -> list[str]:
        """
        Creates a list splitting a string at commas
        Raises `ServerConfLoaderErr` if something goes wrong
        """
        try:
            if not env.strip():
                return []

            items = []
            for item in env.split(","):
                clean_item = item.strip()

                if clean_item:
                    items.append(clean_item)

            return items
        except Exception as e:
            raise ConfLoaderErr(f"couldn't parse list {env}: {e}")

    @staticmethod
    def _fetch_mandatory_as(envname: str, cast: Callable[[str], T]) -> T:
        """
        Fetches a mandatory field from env and casts it with the provided function
        Raises `ServerConfLoaderErr` if the mandatory field isn't on env
        """
        env = os.getenv(envname)

        if env is None:
            raise ConfLoaderErr(f"mandatory env variable {envname} is missing")

        return cast(env)

    @staticmethod
    def _fetch_optional_as(envname: str, cast: Callable[[str], T]) -> Optional[T]:
        """
        Fetches an optional field from env and casts it with the provided function if it isn't None
        """
        env = os.getenv(envname)

        if env is None:
            return env

        return cast(env)

    def load(self) -> ServerConf:
        load_dotenv()

        return ServerConf(
            self._fetch_mandatory_as(self.ENV_DISCORD_TOKEN, str),
            self._fetch_mandatory_as(self.ENV_DISCORD_GUILD, str),
            self._fetch_mandatory_as(self.ENV_DISCORD_LOG_CHANNEL, str),
            self._fetch_mandatory_as(self.ENV_PROCESS_SCRIPT, str),
            self._fetch_optional_as(self.ENV_PROCESS_TIMEOUT, float),
            self._fetch_optional_as(self.ENV_MINECRAFT_PORT, int),
            self._fetch_optional_as(self.ENV_RCON_PORT, int),
            self._fetch_optional_as(self.ENV_RCON_PWD, str),
            self._fetch_optional_as(self.ENV_RCON_TIMEOUT, float),
            self._fetch_optional_as(self.ENV_RCON_MAX_COMM_LEN, int),
            self._fetch_optional_as(self.ENV_RCON_BANNED_COMM, self._list_from_env),
            self._fetch_optional_as(self.ENV_STARTUP_TIMEOUT, float),
            self._fetch_optional_as(self.ENV_IDLE_TIMEOUT, float),
            self._fetch_optional_as(self.ENV_POLLING_INTV, float),
        )
