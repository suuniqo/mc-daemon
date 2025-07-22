import discord

from bot.commands.cog import ServerCommands
from bot.errors import BotErr
from bot.logger.event_logger import EventLogger

from server.domain.event.types import ServerEvent
from server.domain.event.ebus import ServerEventBus
from server.domain.event.membus import MemoryEventBus

from server.factory import ServerDataFactory

from conf.types import GlobalConf

from .mcdaemon_bot import McDaemonBot


class BotFactory:
    @staticmethod
    async def _validate_discord_guild(bot: discord.Client, guild_id: int) -> None:
        try:
            await bot.fetch_guild(guild_id)
        except discord.NotFound:
            raise BotErr(f"guild {guild_id} not found")
        except discord.Forbidden:
            raise BotErr(f"access to guild {guild_id} is forbidden to the bot")
        except discord.HTTPException as e:
            raise BotErr(f"HTTP error while fetching guild {guild_id}: {e}")
        except Exception as e:
            raise BotErr(f"Unexpected error validating guild {guild_id}: {e}")

    @staticmethod
    async def _validate_discord_channel(bot: discord.Client, guild_id: int, channel_id: int) -> None:
        try:
            channel = await bot.fetch_channel(channel_id)

            if not isinstance(channel, discord.TextChannel):
                raise BotErr(f"channel {channel_id} must be a guild TextChannel")

            if getattr(channel, "guild", None) is None or channel.guild.id != guild_id:
                raise BotErr(f"channel {channel_id} must belong to the specified guild {guild_id}")
        except discord.NotFound:
            raise BotErr(f"channel {channel_id} not found")
        except discord.Forbidden:
            raise BotErr(f"access to channel {channel_id} is forbidden to the bot")
        except discord.HTTPException as e:
            raise BotErr(f"HTTP error while fetching channel {channel_id}: {e}")
        except Exception as e:
            raise BotErr(f"Unexpected error validating channel {channel_id}: {e}")

    @staticmethod
    async def make(conf: GlobalConf) -> McDaemonBot:
        """
        Makes a new instance of `McDaemonBot` through `ServerConf`
        """
        intents = discord.Intents.default()
        intents.message_content = True

        bot = McDaemonBot(conf.discord_guild, intents=intents)

        await BotFactory._validate_discord_guild(bot, conf.discord_guild)

        if conf.discord_log_channel is not None:
            await BotFactory._validate_discord_channel(bot, conf.discord_guild, conf.discord_log_channel)
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
