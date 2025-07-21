import discord

from bot.commands.cog import ServerCommands
from bot.logger.event_logger import EventLogger

from server.domain.event.types import ServerEvent
from server.domain.event.ebus import ServerEventBus
from server.domain.event.membus import MemoryEventBus

from server.factory import ServerDataFactory

from conf.types import GlobalConf

from .mcdaemon_bot import McDaemonBot


class BotFactory:
    @staticmethod
    async def make(conf: GlobalConf) -> McDaemonBot:
        """
        Makes a new instance of `McDaemonBot` through `ServerConf`
        """
        intents = discord.Intents.default()
        intents.message_content = True

        bot = McDaemonBot(conf.discord_guild, intents=intents)

        if conf.discord_log_channel:
            # we need memory bus for logging
            ebus = MemoryEventBus(list(ServerEvent))
            logger = EventLogger(bot, ebus, conf.discord_log_channel)
        else:
            ebus = ServerEventBus()
            logger = None

        if logger:
            bot.add_logger(logger)

        data = ServerDataFactory.make(conf, ebus)
        cog = ServerCommands(data, conf.discord_guild)

        await bot.add_cog(cog)

        return bot
