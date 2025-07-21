import subprocess
import logging

from typing import Optional

from .protocol import ServerProc
from .errors import ProcErr


class MinecraftProc(ServerProc):
    STOP_COMMAND = b"/stop\n"

    def __init__(self, startup_script: str, timeout: float) -> None:
        self._startup_script: str = startup_script
        self._timeout: float = timeout
        self._inst: Optional[subprocess.Popen[bytes]] = None
        self._logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def start(self) -> None:
        if self._inst is not None:
            raise ProcErr("Failed to start: process is currently running")

        try:
            self._inst = subprocess.Popen(
                    self._startup_script,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
            )
        except (ValueError | OSError) as e:
            raise ProcErr(f"Failed to start process: {e}")
        except Exception as e:
            raise ProcErr(f"Failed to start process: Unexpected error: {e}")

    def alive(self) -> bool:
        return self._inst is not None and self._inst.poll() is None

    def stop(self) -> None:
        if self._inst is None:
            raise ProcErr("Failed to stop: process isn't currently running")

        if not self.alive():
            self._inst = None
            return

        try:
            self._inst.communicate(input=self.STOP_COMMAND, timeout=self._timeout)
        except subprocess.TimeoutExpired:
            self._logger.warning(f"Timeout reached comunicating stop command to server instance")
        except Exception as e:
            self._logger.error(f"Error communicating stop command to server instance: {e}")

        try:
            self._inst.wait(timeout=self._timeout)
        except subprocess.TimeoutExpired:
            self._logger.warning("Timeout reached waiting for server instance to stop")
            self._logger.warning("Killing instance...")
            self.kill()
        except Exception as e:
            self._logger.warning(f"Error while waiting for server instance to stop: {e}")
            self._logger.warning("Killing instance...")
            self.kill()

    def kill(self) -> None:
        if not self._inst:
            return

        if not self.alive():
            self._inst = None
            return

        try:
            self._inst.kill()
            self._inst.wait(timeout=self._timeout)
        except Exception as e:
            self._logger.critical(f"Error killing instance: {e}")
            self._logger.critical("Instance could be in zombie state, check inmediatly")
        finally:
            self._inst = None

mcproc = MinecraftProc("/lol", 2)
