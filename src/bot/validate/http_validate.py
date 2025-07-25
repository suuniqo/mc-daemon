import aiohttp

class HttpValidate:

    DISCORD_API_BASE = "https://discord.com/api/v10"

    HTTP_OK = 200
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404

    CHANNEL_TYPE_GUILD_TEXT = 0

    @staticmethod
    def _header_from_token(token: str) -> dict[str, str]:
        return {"Authorization": f"Bot {token}"}

    @staticmethod
    async def validate_discord_config(token: str, guild_id: int, channel_ids: list[int]) -> None:
        async with aiohttp.ClientSession(headers=HttpValidate._header_from_token(token)) as session:
            # validate token
            async with session.get(f"{HttpValidate.DISCORD_API_BASE}/users/@me") as resp:
                if resp.status != HttpValidate.HTTP_OK:
                    raise ValueError("Invalid bot token")

            # validate guild
            async with session.get(f"{HttpValidate.DISCORD_API_BASE}/guilds/{guild_id}") as resp:
                if resp.status == HttpValidate.HTTP_FORBIDDEN:
                    raise ValueError("Bot does not have access to the specified guild")
                elif resp.status == HttpValidate.HTTP_NOT_FOUND:
                    raise ValueError("Guild ID not found")

            # validate channels
            for channel_id in channel_ids:
                async with session.get(f"{HttpValidate.DISCORD_API_BASE}/channels/{channel_id}") as resp:
                    if resp.status == HttpValidate.HTTP_FORBIDDEN:
                        raise ValueError(f"Bot does not have access to channel {channel_id}")
                    elif resp.status == HttpValidate.HTTP_NOT_FOUND:
                        raise ValueError(f"Channel {channel_id} not found")
                    elif resp.status == HttpValidate.HTTP_OK:
                        channel_data = await resp.json()

                        if channel_data.get("type") != HttpValidate.CHANNEL_TYPE_GUILD_TEXT:
                            raise ValueError(f"Channel {channel_id} is not a guild text channel")

                        if int(channel_data.get("guild_id", 0)) != guild_id:
                            raise ValueError(f"Channel {channel_id} does not belong to the specified guild")
