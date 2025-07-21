import asyncio
import discord
import logging

from typing import Optional

from discord.channel import TextChannel

from domain.event.membus import MemoryEventBus
from domain.event.types import ServerEvent

from .protocol import BotLogger


class EventLogger(BotLogger):
    def __init__(
        self, client: discord.Client, membus: MemoryEventBus, channel_id: int
    ) -> None:
        self._client: discord.Client = client
        self._membus: MemoryEventBus = membus

        channel = client.get_channel(channel_id)

        if not isinstance(channel, TextChannel):
            raise TypeError("Invalid channel id, should be TextChannel")

        self._channel: TextChannel = channel

        self._task: Optional[asyncio.Task] = None
        self._logger: logging.Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            self._logger.warning("Tried to start logger when it was running")
            return

        self._task = asyncio.create_task(self._logger_loop())

    async def _logger_loop(self) -> None:
        while self._client.is_closed():
            embed = None

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
                        title="The server is starting up... 📊",
                        color=discord.Color.blue(),
                    )
                case ServerEvent.CLOSING:
                    embed = discord.Embed(
                        title="The server is shutting down... 📊",
                        color=discord.Color.blue(),
                    )
                case ServerEvent.CRASHED:
                    embed = discord.Embed(
                        title="The server has crashed ❌",
                        description="Attempting to restart...",
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
                        description="Shutting down...",
                        color=discord.Color.yellow(),
                    )

            await self._channel.send(embed=embed)
