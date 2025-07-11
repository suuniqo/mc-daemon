import os
import sys
import discord
import threading
import subprocess
import time
import psutil
import asyncio
from mcipc.rcon.je import Client

from typing import cast, Optional
from enum import Enum
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import tasks

class ServerStatus(Enum):
    CLOSED = 0
    OPEN = 1
    OPENING = 2
    CLOSING = 3

    def __str__(self) -> str:
        match self:
            case ServerStatus.CLOSED:
                return "closed"
            case ServerStatus.OPEN:
                return "open"
            case ServerStatus.OPENING:
                return "opening"
            case ServerStatus.CLOSING:
                return "closing"

class ServerConn:
    PORT = 25565

    @staticmethod
    def is_empty() -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_ESTABLISHED and conn.laddr.port == ServerConn.PORT:
                return False
        return True

    @staticmethod
    def is_open() -> bool:
        for conn in psutil.net_connections(kind='tcp'):
            if isinstance(conn.laddr, tuple) and len(conn.laddr) == 0:
                continue
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == ServerConn.PORT:
                return True
        return False

class ServerEnv:
    ENVNAME_SCRIPT = "STARTUP_SCRIPT"
    ENVNAME_TOKEN = "DISCORD_TOKEN"
    ENVNAME_GUILD = "GUILD_ID"
    ENVNAME_RCONPWD = "RCON_PASSWORD"

    def __init__(self) -> None:
        try_fetch = lambda envname: os.getenv(envname) or sys.exit(f"couldn't fetch {envname} from .env")

        load_dotenv()
        self.token: str = try_fetch(ServerEnv.ENVNAME_TOKEN)
        self.script: str = try_fetch(ServerEnv.ENVNAME_SCRIPT)
        self.guild: discord.Object = discord.Object(int(try_fetch(ServerEnv.ENVNAME_GUILD)))
        self.rconpwd: str = try_fetch(ServerEnv.ENVNAME_RCONPWD)

class ServerRCON:
    PORT = 25575
    HOST = "127.0.0.1"
    TIMEOUT = 15

    def __init__(self, pwd: str) -> None:
        self.pwd: str = pwd

    def command(self, comm: str) -> tuple[bool, str]:
        try:
            with Client(ServerRCON.HOST, ServerRCON.PORT, passwd=self.pwd, timeout=ServerRCON.TIMEOUT) as client:
                return True, client.run(comm)
        except Exception as e:
            return False, f"RCON error: {str(e)}"

class ServerCntl:
    PROC_TIMEOUT = 5
    COMM_MAXLEN = 256
    STOP_COMMAND = b"/stop\n"

    def __init__(self, script: str, rcon_pwd: str) -> None:
        self._rcon: ServerRCON = ServerRCON(rcon_pwd)
        self._lock: threading.Lock = threading.Lock()
        self._status: ServerStatus = ServerStatus.CLOSED
        self._inst: Optional[subprocess.Popen[bytes]] = None
        self._script: str = script

    def status(self) -> ServerStatus:
        with self._lock:
            return self._status

    def try_start(self) -> bool:
        with self._lock:
            if not self._inst is None or self._status != ServerStatus.CLOSED:
                return False

            self._status = ServerStatus.OPENING
            self._inst = subprocess.Popen(
                    self._script,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
            )
            return True

    def try_stop(self):
        with self._lock:
            if self._inst is None or self._status != ServerStatus.OPEN or self._inst.stdin is None:
                return

            if not self._inst.poll() is None:
                self._inst = None
                self._status = ServerStatus.CLOSED
                return

            self._status = ServerStatus.CLOSING

            try:
                self._inst.communicate(input=ServerCntl.STOP_COMMAND, timeout=ServerCntl.PROC_TIMEOUT)
            except subprocess.TimeoutExpired:
                self._inst.kill()

            try:
                self._inst.wait(timeout=ServerCntl.PROC_TIMEOUT)
            except subprocess.TimeoutExpired:
                self._inst.kill()

            self._inst = None
            self._status = ServerStatus.CLOSED

            return

    def wait_open(self) -> None:
        while not ServerConn.is_open():
            time.sleep(1)

        with self._lock:
            self._status = ServerStatus.OPEN

    def crashed(self) -> bool:
        with self._lock:
            if self._inst is None:
                return False
            return not self._inst.poll() is None

    def command(self, comm: str) -> tuple[bool, str]:
        if not comm.strip() or len(comm) > 256:
            return False, "invalid command format"
                            
        illegal_comms = ["/stop"]

        for icomm in illegal_comms:
            if icomm in comm.lower():
                return False, f"command {icomm} not allowed"

        return self._rcon.command(comm)

class ServerManager(discord.Client):
    EMPTY_SERVER_TIMEOUT = 60 * 5

    def __init__(self, env: ServerEnv, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.env = env
        self.cntl = ServerCntl(env.script, env.rconpwd)
        self.stamp = None
        self.locked = False
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync(guild=self.env.guild)

    async def autoshutdown_wait(self) -> None:
        while not self._autoshutdown.is_running():
            await asyncio.sleep(1)

    def autoshutdown_start(self) -> None:
        if not self._autoshutdown.is_running():
            self._autoshutdown.start()

    def autoshutdown_stop(self) -> None:
        if self._autoshutdown.is_running():
            self._autoshutdown.stop()

    @tasks.loop(minutes=1)
    async def _autoshutdown(self) -> None:
        status = self.cntl.status()

        if status != ServerStatus.OPEN or not ServerConn.is_empty():
            self.stamp = None
            return;

        if self.stamp == None:
            self.stamp = time.time()
        elif time.time() - self.stamp >= ServerManager.EMPTY_SERVER_TIMEOUT or self.cntl.crashed():
            self.cntl.try_stop()
            self._autoshutdown.stop()
            self.stamp = None


intents=discord.Intents.default()
intents.message_content = True

bot = ServerManager(ServerEnv(), intents=intents)

@bot.event
async def on_ready():
    pass

@bot.tree.command(name="help", description="View available commands")
async def help(inter: discord.Interaction):
    embed = discord.Embed(
        title="Available commands 📋",
        description=(
            "- `/start` Tries to start the server\n"
            "- `/status` Shows the server status\n"
            "- `/lock` Locks and closes the server (admin)\n"
            "- `/unlock` Unlocks the server (admin)\n"
            "- `/inject` Executes the provided minecraft command in the server (admin)"
        ),
        color=discord.Color.yellow()
    )

    await inter.response.send_message(embed=embed)

@bot.tree.command(name="start", description="Tries to start the server")
async def start(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.locked:
        embed = discord.Embed(
            title="The server has been locked by admins ❌",
            color=discord.Color.red()
        )

        await inter.response.send_message(embed=embed)
        return

    if mng.cntl.try_start():
        await inter.response.defer()
        await asyncio.to_thread(mng.cntl.wait_open)
        mng.autoshutdown_start()

        embed = discord.Embed(
            title=f"The server is ready {inter.user.mention}! ✅",
            color=discord.Color.green()
        )

        await inter.followup.send(embed=embed)

        return

    status = mng.cntl.status()

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

    status = mng.cntl.status()
    stamp = mng.stamp
    
    if status == ServerStatus.OPEN and stamp != None:
        elapsed = time.time() - stamp
        remaining = max(0, mng.EMPTY_SERVER_TIMEOUT - elapsed)

        mins = int(remaining // 60)
        secs = int(remaining % 60)

        embed = discord.Embed(
            title=f"The server is {status} but empty ⚠️",
            description=f"It will close in {mins} minutes and {secs} seconds if nobody joins",
            color=discord.Color.yellow(),
        )

        await inter.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title=f"The server is {status} 📊",
            color=discord.Color.blue()
        )
        await inter.response.send_message(embed=embed)

@app_commands.default_permissions(discord.Permissions(administrator=True))
@bot.tree.command(name="lock", description="Locks and closes the server")
async def lock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.locked:
        embed = discord.Embed(
            title="The server was already locked ✅",
            color=discord.Color.green()
        )
        await inter.response.send_message(embed=embed)
        return

    mng.locked = True

    await inter.response.defer()

    status = mng.cntl.status()

    if status == ServerStatus.OPEN:
        mng.cntl.try_stop()
        mng.autoshutdown_stop()
    elif status == ServerStatus.OPENING:
        await mng.autoshutdown_wait()
        mng.cntl.try_stop()
        mng.autoshutdown_stop()

    embed = discord.Embed(
        title="The server has been locked 🔒",
        color=discord.Color.yellow()
    )
    await inter.followup.send(embed=embed)

@app_commands.default_permissions(discord.Permissions(administrator=True))
@bot.tree.command(name="unlock", description="Unlocks the server")
async def unlock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    embed = None

    if not mng.locked:
        embed = discord.Embed(
            title="The server was already locked ✅",
            color=discord.Color.green()
        )
    else:
        mng.locked = False
        embed = discord.Embed(
            title="The server has been unlocked 🔓",
            color=discord.Color.yellow()
        )

    await inter.response.send_message(embed=embed)

@app_commands.rename(comm="command")
@app_commands.describe(comm="Command to execute")
@app_commands.default_permissions(discord.Permissions(administrator=True))
@bot.tree.command(name="inject", description="Executes the provided minecraft command in the server")
async def inject(inter: discord.Interaction, comm: str) -> None:
    mng = cast(ServerManager, inter.client)

    status = mng.cntl.status()

    if status != ServerStatus.OPEN:
        embed = discord.Embed(
            title=f"It's not posible to execute commands, the server is {status} ❌",
            color=discord.Color.red(),
        )
        await inter.response.send_message(embed=embed)
        return

    await inter.response.defer()

    success, resp = mng.cntl.command(comm)

    embed = None

    if success:
        embed = discord.Embed(
            title=f"The command was executed correctly ✅",
            description=f"`{resp}`",
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title=f"Couldn't execute command ❌",
            description=f"`{resp}`",
            color=discord.Color.red(),
        )
        await inter.followup.send(
                )

    await inter.followup.send(embed=embed)

bot.run(bot.env.token)
