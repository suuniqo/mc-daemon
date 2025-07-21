from typing import Optional


class GlobalConf:
    def __init__(
        self,
        discord_token: str,
        discord_guild: int,
        process_script: str,
        process_timeout: Optional[float],
        discord_log_channel: Optional[int],
        minecraft_port: Optional[int],
        rcon_port: Optional[int],
        rcon_pwd: Optional[str],
        rcon_timeout: Optional[float],
        rcon_max_comm_len: Optional[int],
        rcon_banned_comm: Optional[list[str]],
        startup_timeout: Optional[float],
        idle_timeout: Optional[float],
        polling_intv: Optional[float],
    ) -> None:

        # discord config
        self.discord_token: str = discord_token
        self.discord_guild: int = discord_guild

        # process config
        self.process_script: str = process_script
        self.process_timeout: float = process_timeout or 4.0

        # logger config
        self.discord_log_channel: Optional[int] = discord_log_channel or None

        # conn config
        self.minecraft_port: int = minecraft_port or 25565

        # rcon config
        self.rcon_port: int = rcon_port or 25575
        self.rcon_pwd: Optional[str] = rcon_pwd or None
        self.rcon_timeout: float = rcon_timeout or 16.0
        self.rcon_max_comm_len: int = rcon_max_comm_len or 256
        self.rcon_banned_comm: list[str] = rcon_banned_comm or []

        # cntl config
        self.startup_timeout: float = startup_timeout or 2.0 * 60.0

        # mntr config
        self.idle_timeout: float = idle_timeout or 5.0 * 60.0
        self.polling_intv: float = polling_intv or 60.0
