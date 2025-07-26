# mc-daemon
Enhance the experience of managing a self-hosted Minecraft server.

## What is mc-daemon?

`mc-daemon` is a highly extensible service designed to improve the experience of both administrators managing the server, and players interacting with it.

It's features are organized in two main layers:
- **Embedded Layer**: Automates routine tasks such as detecting server crashes and shutting down the server when it's empty for a while.
- **Discord Integration Layer**: Provides both players and admins with a suit of convenient slash commands for seamlessly managing the server from Discord, as well as event logging on text channels.

For instance, instead of having to manually open the server each time a player wants to join, users can simply use the `/start` command on Discord to open the server themselves.

With the use of dependency injection and an event-driven architecture, implementing new features, adding new slash commands, or even adapting the project to another game is really straightforward. Feel free to fork the project and customize it to your needs.

## Features
This section provides a detailed overview of the app's functionalities

### Embedded Layer
This layer is responsible for directly managing and controlling the Minecraft server instance.

It provides the server administrators with:
- Handling of unexpected conditions such as server crashes or freezes, where the process is automatically terminated, cleaned up and restarted.
- Server activity monitoring, with configurable threshholds to define how long the server needs to remain empty before triggering a shutdown.

### Discord Integration Layer
This layer enables both players and administrators to interact with the server process through Discord slash commans. Commands are divided into two categories:
- **Public Commands:** Available for everyone, wether in a server (guild) or direct messages (DMs).
- **Private Commands:** Restricted to guild administratora of the specified guild. This prevents someone from just creating a new guild, adding the bot and gaining unautorized control.

The bot provides the following public commands:

- `/status` Reports the current server status

![status command demo](.github/assets/comm-status.png)
