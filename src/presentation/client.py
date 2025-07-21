import discord

class BotClient(discord.Client):
    def __init__(self, , *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.conf = ServerConf(env.token, env.guild)
        self.cntl = ServerCntl(env.script)
        self.rcon = ServerRcon(env.rconpwd)
        self.mntr = ServerMntr(self.cntl)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()
        await self.tree.sync(guild=self.conf.guild)
