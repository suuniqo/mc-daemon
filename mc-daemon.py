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
                return "cerrado"
            case ServerStatus.OPEN:
                return "abierto"
            case ServerStatus.OPENING:
                return "abriéndose"
            case ServerStatus.CLOSING:
                return "cerrándose"

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
    TIMEOUT = 5

    def __init__(self, pwd: str) -> None:
        self.pwd: str = pwd

    def command(self, comm: str) -> tuple[bool, str]:
        try:
            with Client(ServerRCON.HOST, ServerRCON.PORT, passwd=self.pwd, timeout=ServerRCON.TIMEOUT) as client:
                return False, client.run(comm)
        except Exception as e:
            return True, f"RCON error: {str(e)}"

class ServerCntl:
    PROC_TIMEOUT = 5
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
        return self._rcon.command(comm)

class ServerManager(discord.Client):
    EMPTY_SERVER_TIMEOUT = 60 * 5

    def __init__(self, startup_script: str, rcon_pwd: str, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.cntl = ServerCntl(startup_script, rcon_pwd)
        self.stamp = None
        self.blocked = False
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def autoshutdown_wait(self) -> None:
        while not self._autoshutdown.is_running():
            await asyncio.sleep(1)

    def autoshutdown_start(self) -> None:
        if not self._autoshutdown.is_running():
            self._autoshutdown.start()

    def autoshutdown_stop(self) -> None:
        if self._autoshutdown.is_running():
            self._autoshutdown.stop()

    @tasks.loop(seconds=60)
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

env = ServerEnv()
bot = ServerManager(env.script, env.rconpwd, intents=intents)

@bot.tree.command(name="help", description="Consulta los comandos disponibles")
@app_commands.guild_only()
@app_commands.guilds(env.guild)
async def help(inter: discord.Interaction):
    await inter.response.send_message(
            "**📋 Comandos disponibles:**\n"
            "- `/start` Intenta iniciar el server\n"
            "- `/status` Muestra el status del server\n"
            "- `/lock` Apaga y bloquea el server (admin)\n"
            "- `/unlock` Desbloquea el server (admin)\n"
            "- `/inject` Ejecuta un comando el server (admin)"
            )

@bot.tree.command(name="start", description="Intenta iniciar el server")
@app_commands.guild_only()
@app_commands.guilds(env.guild)
async def start(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.blocked:
        await inter.response.send_message(f"❌ El server ha sido bloqueado por los admins.")
        return

    if mng.cntl.try_start():
        await inter.response.defer()
        await asyncio.to_thread(mng.cntl.wait_open)
        mng.autoshutdown_start()
        await inter.followup.send(f"✅ ¡El server está listo {inter.user.mention}!")
        return

    status = mng.cntl.status()

    match status:
        case ServerStatus.OPEN | ServerStatus.OPENING:
            await inter.response.send_message(f"✅ El server ya está {status}.")
        case ServerStatus.CLOSING:
            await inter.response.send_message(f"⚠️ El server está {status}, espera porfavor...")
        case ServerStatus.CLOSED:
            await inter.response.send_message(f"❌ Inténtalo de nuevo porfavor")

@bot.tree.command(name="status", description="Muestra el status del server")
@app_commands.guild_only()
@app_commands.guilds(env.guild)
async def status(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    status = mng.cntl.status()
    stamp = mng.stamp
    
    if status == ServerStatus.OPEN and stamp != None:
        elapsed = time.time() - stamp
        remaining = max(0, mng.EMPTY_SERVER_TIMEOUT - elapsed)

        mins = int(remaining // 60)
        secs = int(remaining % 60)

        await inter.response.send_message(
                f"⚠️ El server está {status} pero vacío.\n"
                f"Se cerrará en {mins} minutos y {secs} segundos si nadie se une."
                )
    else:
        await inter.response.send_message(f"📊 El server está {status}.")

@bot.tree.command(name="lock", description="Apaga y bloquea el server")
@app_commands.guild_only()
@app_commands.guilds(env.guild)
@app_commands.default_permissions(discord.Permissions(administrator=True))
async def lock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if mng.blocked:
        await inter.response.send_message(f"✅ El server ya estaba bloqueado.")
        return

    mng.blocked = True

    await inter.response.defer()

    status = mng.cntl.status()

    if status == ServerStatus.OPEN:
        mng.cntl.try_stop()
        mng.autoshutdown_stop()
    elif status == ServerStatus.OPENING:
        await mng.autoshutdown_wait()
        mng.cntl.try_stop()
        mng.autoshutdown_stop()

    await inter.followup.send(f"🔒 El server ha sido bloqueado.")

@app_commands.guild_only()
@app_commands.guilds(env.guild)
@app_commands.default_permissions(discord.Permissions(administrator=True))
@bot.tree.command(name="unlock", description="Desbloquea el server")
async def unlock(inter: discord.Interaction) -> None:
    mng = cast(ServerManager, inter.client)

    if not mng.blocked:
        await inter.response.send_message(f"✅ El server ya estaba desbloqueado.")
        return

    mng.blocked = False
    await inter.response.send_message(f"🔓 El server ha sido desbloqueado.")

@bot.tree.command(name="inject", description="Ejecuta un comando el server.")
@app_commands.rename(comm="command")
@app_commands.describe(comm="Comando a ejecutar.")
@app_commands.guild_only()
@app_commands.guilds(env.guild)
@app_commands.default_permissions(discord.Permissions(administrator=True))
async def inject(inter: discord.Interaction, comm: str) -> None:
    mng = cast(ServerManager, inter.client)

    status = mng.cntl.status()

    if status != ServerStatus.OPEN:
        await inter.response.send_message(f"❌ No es posible inyectar comandos, el server está {status}.")
        return

    await inter.response.defer()

    err, resp = mng.cntl.command(comm)

    if not err:
        await inter.followup.send(
                f"✅ El comando se ejecuto correctamente:\n"
                f"`{resp}`"
                )
    else:
        await inter.followup.send(
                f"❌ No se pudo ejecutar el comando:\n"
                f"`{resp}`"
                )
        


bot.run(env.token)
