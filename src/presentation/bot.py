import discord

class ServerManager(discord.Client):
    EMPTY_SERVER_TIMEOUT = 60 * 5

    def __init__(self, env: ServerEnv, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.conf = ServerConf(env.token, env.guild)
        self.cntl = ServerCntl(env.script)
        self.rcon = ServerRcon(env.rconpwd)
        self.mntr = ServerMntr(self.cntl)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()
        await self.tree.sync(guild=self.conf.guild)

bot = ServerManager.make()

@bot.tree.command(name="help", description="View available commands")
async def help(inter: discord.Interaction):
    await inter.response.send_message(embed=discord.Embed(
        title="Available commands 📋",
        description=(
            "- `/start` Tries to start the server\n"
            "- `/status` Shows the server status\n"
            "- `/lock` Locks and closes the server (admin)\n"
            "- `/unlock` Unlocks the server (admin)\n"
            "- `/inject` Executes the provided command in the server (admin)"
        ),
        color=discord.Color.yellow()
    ))

@bot.tree.command(name="start", description="Tries to start the server")
async def start(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.cntl.locked:
        await inter.response.send_message(embed=discord.Embed(
            title="The server has been locked by admins ❌",
            color=discord.Color.red()
        ))
        return

    if mng.cntl.try_start():
        await inter.response.defer()
        
        opened = await mng.cntl.wait_open()

        if not opened:
            await inter.response.send_message(embed=discord.Embed(
                title="The server crashed on startup ❌",
                color=discord.Color.red()
            ))

        mng.mntr.autoshutdown_start()

        await inter.followup.send(embed=discord.Embed(
            title=f"The server is ready ✅",
            description=f"You can join now {inter.user.mention}",
            color=discord.Color.green()
        ))

        return

    status = mng.cntl.status

    embed = None

    match status:
        case ServerStatus.OPEN | ServerStatus.OPENING:
            embed = discord.Embed(
                title=f"The server is already {status} ✅",
                color=discord.Color.green()
            )
        case ServerStatus.CLOSING:
            embed = discord.Embed(
                title=f"The server is {status}, please stand by ⚠️",
                color=discord.Color.yellow()
            )
        case ServerStatus.CLOSED:
            embed = discord.Embed(
                title="Please try again ❌",
                color=discord.Color.red()
            )

    await inter.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Shows the server status")
async def status(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    status = mng.cntl.status
    stamp = mng.mntr.stamp
    
    if status == ServerStatus.OPEN and stamp != None:
        elapsed = time.time() - stamp
        remaining = max(0, mng.EMPTY_SERVER_TIMEOUT - elapsed)

        mins = int(remaining // 60)
        secs = int(remaining % 60)

        await inter.response.send_message(embed=discord.Embed(
            title=f"The server is {status} but empty ⚠️",
            description=f"It will close in {mins} minutes and {secs} seconds if nobody joins",
            color=discord.Color.yellow(),
        ))
    else:
        await inter.response.send_message(embed=discord.Embed(
            title=f"The server is {status} 📊",
            color=discord.Color.blue()
        ))

@bot.tree.command(name="lock", description="Locks and closes the server")
@app_commands.guild_only()
@app_commands.guilds(bot.conf.guild)
@app_commands.default_permissions(discord.Permissions(administrator=True))
async def lock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.cntl.locked:
        await inter.response.send_message(embed=discord.Embed(
            title="The server was already locked ✅",
            color=discord.Color.green()
        ))
        return

    mng.cntl.locked = True

    await inter.response.defer()

    status = mng.cntl.status

    if status == ServerStatus.OPEN:
        mng.cntl.try_stop()
        mng.mntr.autoshutdown_stop()
    elif status == ServerStatus.OPENING:
        await mng.mntr.autoshutdown_wait()
        mng.cntl.try_stop()
        mng.mntr.autoshutdown_stop()

    await inter.followup.send(embed=discord.Embed(
        title="The server has been locked 🔒",
        color=discord.Color.yellow()
    ))

@bot.tree.command(name="unlock", description="Unlocks the server")
@app_commands.guild_only()
@app_commands.guilds(bot.conf.guild)
@app_commands.default_permissions(discord.Permissions(administrator=True))
async def unlock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    embed = None

    if not mng.cntl.locked:
        embed = discord.Embed(
            title="The server was already unlocked ✅",
            color=discord.Color.green()
        )
    else:
        mng.cntl.locked = False
        embed = discord.Embed(
            title="The server has been unlocked 🔓",
            color=discord.Color.yellow()
        )

    await inter.response.send_message(embed=embed)

@bot.tree.command(name="inject", description="Executes the provided command in the server")
@app_commands.guild_only()
@app_commands.guilds(bot.conf.guild)
@app_commands.rename(comm="command")
@app_commands.describe(comm="Command to execute")
@app_commands.default_permissions(discord.Permissions(administrator=True))
async def inject(inter: discord.Interaction, comm: str) -> None:
    mng = cast(ServerManager, inter.client)

    status = mng.cntl.status

    if status != ServerStatus.OPEN:
        await inter.response.send_message(embed=discord.Embed(
            title=f"It's not posible to execute commands, the server is {status} ❌",
            color=discord.Color.red(),
        ))
        return

    await inter.response.defer()

    success, resp = mng.rcon.command(comm)

    embed = None

    if success:
        embed = discord.Embed(
            title=f"The command was executed correctly ✅",
            description=f"`{resp}`" if resp else None,
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title=f"Couldn't execute command ❌",
            description=f"`{resp}`" if resp else None,
            color=discord.Color.red(),
        )

    await inter.followup.send(embed=embed)
