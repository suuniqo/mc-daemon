import discord

from discord import app_commands
from discord.ext import commands

from server.domain.cntl.types import ServerStatus
from server.services.rcon.errors import CommErr, RconErr

from server.types import ServerData


class ServerCommands(commands.Cog):
    def __init__(self, data: ServerData, guild_id: int) -> None:
        self._server: ServerData = data
        self._locked: bool = False
        self._guild_id: int = guild_id

    async def _validate_guild(self, inter: discord.Interaction) -> bool:
        """
        Returns whether the current guild is the guild id provided by the user for privileged commands
        """
        if inter.guild_id != self._guild_id:
            await inter.response.send_message(
                embed=discord.Embed(
                    title="This command can only be used by admins on a specific guild ❌",
                    color=discord.Color.red(),
                )
            )
            return False
        return True

    @app_commands.command(name="help", description="View available commands")
    async def help(self, inter: discord.Interaction):
        await inter.response.send_message(
            embed=discord.Embed(
                title="Available commands 📋",
                description=(
                    "- `/start` Tries to start the server\n"
                    "- `/status` Shows the server status\n"
                    "- `/lock` Locks and closes the server (admin)\n"
                    "- `/unlock` Unlocks the server (admin)\n"
                    "- `/inject` Executes the provided command in the server (admin)"
                ),
                color=discord.Color.yellow(),
            )
        )

    @app_commands.command(name="start", description="Tries to start the server")
    async def start(self, inter: discord.Interaction) -> None:
        if self._locked:
            await inter.response.send_message(
                embed=discord.Embed(
                    title="The server has been locked by admins ❌",
                    color=discord.Color.red(),
                )
            )
            return

        srv = self._server

        if srv.cntl.try_open():
            await inter.response.defer()

            opened = await srv.cntl.wait_open()

            if not opened:
                embed = discord.Embed(
                    title="The server hung on startup ❌", color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"The server is ready ✅",
                    description=f"You can join now {inter.user.mention}",
                    color=discord.Color.green(),
                )

            await inter.followup.send(embed=embed)
            return

        status = srv.cntl.status()

        match status:
            case ServerStatus.OPEN | ServerStatus.OPENING:
                embed = discord.Embed(
                    title=f"The server is already {status} ✅",
                    color=discord.Color.green(),
                )
            case ServerStatus.CLOSING:
                embed = discord.Embed(
                    title=f"The server is {status}, please stand by ⚠️",
                    color=discord.Color.yellow(),
                )
            case ServerStatus.CLOSED:
                embed = discord.Embed(
                    title="Please try again ❌", color=discord.Color.red()
                )

        await inter.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Shows the server status")
    async def status(self, inter: discord.Interaction) -> None:
        srv = self._server

        status = srv.cntl.status()
        remaining = srv.mntr.timeout_in()

        if status != ServerStatus.OPEN:
            await inter.response.send_message(
                embed=discord.Embed(
                    title=f"The server is {status} 📊", color=discord.Color.blue()
                )
            )
            return

        if remaining:
            mins = int(remaining // 60)
            secs = int(remaining % 60)

            embed = discord.Embed(
                title=f"The server is {status} but empty ⚠️",
                description=f"It will close in {mins} minutes and {secs} seconds if nobody joins",
                color=discord.Color.yellow(),
            )
        else:
            embed = discord.Embed(
                title=f"The server is {status} 📊",
                description=f"There are currently {srv.conn.client_count()} players online",
                color=discord.Color.blue(),
            )

        await inter.response.send_message(embed=embed)

    @app_commands.command(name="lock", description="Locks and closes the server")
    @app_commands.guild_only()
    @app_commands.default_permissions(discord.Permissions(administrator=True))
    async def lock(self, inter: discord.Interaction) -> None:
        if not await self._validate_guild(inter):
            return

        if self._locked:
            await inter.response.send_message(
                embed=discord.Embed(
                    title="The server is already locked ✅", color=discord.Color.green()
                )
            )
            return

        srv = self._server
        status = srv.cntl.status()

        if status == ServerStatus.OPENING or status == ServerStatus.CLOSING:
            await inter.response.send_message(
                embed=discord.Embed(
                    title=f"The server can't be locked because it's {status} ❌",
                    description="Please try again when the operation finishes",
                    color=discord.Color.red(),
                )
            )
            return

        self._locked = True

        await inter.response.defer()

        if status == ServerStatus.OPEN:
            srv.cntl.try_close()

        await inter.followup.send(
            embed=discord.Embed(
                title="The server has been locked 🔒", color=discord.Color.yellow()
            )
        )

    @app_commands.command(name="unlock", description="Unlocks the server")
    @app_commands.guild_only()
    @app_commands.default_permissions(discord.Permissions(administrator=True))
    async def unlock(self, inter: discord.Interaction) -> None:
        if not await self._validate_guild(inter):
            return

        if not self._locked:
            embed = discord.Embed(
                title="The server is already unlocked ✅", color=discord.Color.green()
            )
        else:
            self._locked = False
            embed = discord.Embed(
                title="The server has been unlocked 🔓", color=discord.Color.yellow()
            )

        await inter.response.send_message(embed=embed)

    @app_commands.command(
        name="inject", description="Executes the provided command in the server"
    )
    @app_commands.guild_only()
    @app_commands.rename(comm="command")
    @app_commands.describe(comm="Command to execute")
    @app_commands.default_permissions(discord.Permissions(administrator=True))
    async def inject(self, inter: discord.Interaction, comm: str) -> None:
        if not await self._validate_guild(inter):
            return

        srv = self._server
        status = srv.cntl.status()

        if status != ServerStatus.OPEN:
            await inter.response.send_message(
                embed=discord.Embed(
                    title=f"It's not possible to execute commands, the server is {status} ❌",
                    color=discord.Color.red(),
                )
            )
            return

        await inter.response.defer()

        embed = discord.Embed(
            title="An unexpected error occurred ❌",
            color=discord.Color.red(),
        )

        try:
            resp = srv.rcon.execute(comm)

            embed = discord.Embed(
                title=f"The command was executed correctly ✅",
                description=f"`{resp}`" if resp else None,
                color=discord.Color.green(),
            )
        except CommErr as e:
            embed = discord.Embed(
                title=f"The provided command is invalid ❌",
                description=str(e),
                color=discord.Color.red(),
            )
        except RconErr as e:
            embed = discord.Embed(
                title=f"Couldn't execute command ❌",
                description=str(e),
                color=discord.Color.red(),
            )
        except Exception as e:
            embed = discord.Embed(
                title=f"An unexpected error occurred ❌",
                description=str(e),
                color=discord.Color.red(),
            )
        finally:
            await inter.followup.send(embed=embed)
