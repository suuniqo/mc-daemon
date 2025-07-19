from typing import Optional


class ServerConf:
    def __init__(
        self,
        discord_token: str,
        discord_guild: str,
        discord_log_channel: str,
        process_script: str,
        process_timeout: Optional[int],
        minecraft_port: Optional[int],
        rcon_port: Optional[int],
        rcon_pwd: Optional[str],
        rcon_timeout: Optional[int],
        rcon_max_comm_len: Optional[int],
        rcon_banned_comm: Optional[list[str]],
        empty_timeout: Optional[int],
    ) -> None:

        # discord config
        self.discord_token: str = discord_token
        self.discord_guild: str = discord_guild
        self.discord_log_channel: str = discord_log_channel

        # process config
        self.process_script: str = process_script
        self.process_timeout: int = process_timeout or 4

        # conn config
        self.minecraft_port: int = minecraft_port or 25565

        # rcon config
        self.rcon_port: int = rcon_port or 25575
        self.rcon_pwd: Optional[str] = rcon_pwd or None
        self.rcon_timeout: int = rcon_timeout or 16
        self.rcon_max_comm_len: int = rcon_max_comm_len or 256
        self.rcon_banned_comm: list[str] = rcon_banned_comm or []

        # monitor config
        self.empty_timeout: int = empty_timeout or 5 * 60
