import discord

from discord.ext import commands

from bot.logger.protocol import BotLogger

class McDaemonBot(commands.Bot):
    def __init__(self, guild_id: int, *, intents: discord.Intents) -> None:
        self._loggers: list[BotLogger] = []
        self._guild: discord.Object = discord.Object(id=guild_id)

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for logger in self._loggers:
            logger.start()

        await self.tree.sync()
        await self.tree.sync(guild=self._guild)

    async def close(self) -> None:
        for logger in self._loggers:
            logger.stop()

        await super().close()

    def add_logger(self, logger: BotLogger) -> None:
        """
        Adds a new logger to the list
        """
        self._loggers.append(logger)
