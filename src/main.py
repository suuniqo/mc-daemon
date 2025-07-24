import asyncio
import logging

from bot.factory import BotFactory
from conf.loader.env_loader import EnvConfLoader


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s][%(asctime)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def main() -> None:
    configure_logging()

    conf = EnvConfLoader.load()
    bot = await BotFactory.make(conf)

    try:
        await bot.start(conf.discord_token)
    except KeyboardInterrupt:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
