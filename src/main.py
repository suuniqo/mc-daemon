import asyncio

from bot.factory import BotFactory
from conf.loader.env_loader import EnvConfLoader


async def main() -> None:
    conf = EnvConfLoader.load()
    bot  = await BotFactory.make(conf)

    bot.run(conf.discord_token)

if __name__ == "__main__":
    asyncio.run(main())
