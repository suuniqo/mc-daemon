import asyncio
import discord
import logging

from typing import Optional

from discord.channel import TextChannel

from server.domain.event.membus import MemoryEventBus
from server.domain.event.types import ServerEvent

from .protocol import BotLogger


class EventLogger(BotLogger):
    def __init__(
        self, client: discord.Client, membus: MemoryEventBus, channel_id: int
    ) -> None:
        self._client: discord.Client = client
        self._membus: MemoryEventBus = membus

        self._channel_id: int = channel_id

        self._task: Optional[asyncio.Task] = None
        self._logger: logging.Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def _fetch_channel(self) -> Optional[TextChannel]:
        """
        Tries to fetch the channel, returns None if the channel isn't a `discord.TextChannel`
        """
        try:
            channel = await self._client.fetch_channel(self._channel_id)

            if isinstance(channel, TextChannel):
                return channel
            return None
        except Exception as e:
            self._logger.error(f"Error validating channel: {e}")
            return None

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            self._logger.warning("Tried to start logger while already running")
            return

        self._task = asyncio.create_task(self._logger_loop())

    def stop(self) -> None:
        if self._task is None or self._task.done():
            self._task = None
            self._logger.warning("Tried to stop logger while not running yet")
            return

        self._task.cancel()

    async def _logger_loop(self) -> None:
        try:
            while (channel := await self._fetch_channel()) is not None:
                match await self._membus.pop():
                    case ServerEvent.OPENED:
                        embed = discord.Embed(
                            title="The server has successfully opened ✅",
                            color=discord.Color.green(),
                        )
                    case ServerEvent.CLOSED:
                        embed = discord.Embed(
                            title="The server has shut down successfully ✅",
                            color=discord.Color.green(),
                        )
                    case ServerEvent.OPENING:
                        embed = discord.Embed(
                            title="The server is starting up 📊",
                            color=discord.Color.blue(),
                        )
                    case ServerEvent.CLOSING:
                        embed = discord.Embed(
                            title="The server is shutting down 📊",
                            color=discord.Color.blue(),
                        )
                    case ServerEvent.CRASHED:
                        embed = discord.Embed(
                            title="The server has crashed ❌",
                            description="Restart will begin shortly",
                            color=discord.Color.red(),
                        )
                    case ServerEvent.HUNG:
                        embed = discord.Embed(
                            title="The server has become unresponsive during startup ❌",
                            description="Admins should investigate the issue",
                            color=discord.Color.red(),
                        )
                    case ServerEvent.OCCUPIED:
                        embed = discord.Embed(
                            title="The server is now occupied ✅",
                            description="Timeout has been cancelled",
                            color=discord.Color.green(),
                        )
                    case ServerEvent.EMPTY:
                        embed = discord.Embed(
                            title="The server is now empty ⚠️",
                            description="It will shut down soon if not occupied",
                            color=discord.Color.yellow(),
                        )
                    case ServerEvent.IDLE:
                        embed = discord.Embed(
                            title="The server has timed out due to inactivity ⚠️",
                            description="Shutdown will begin shortly",
                            color=discord.Color.yellow(),
                        )
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    self._logger.error(f"There was an error logging an event: {e}")
        except asyncio.CancelledError:
            pass
