import atexit
import logging
import os
import select
import signal
import socket
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
_STOP_TIMEOUT = 5


class PyLSPProvider:
    """A provider for the PyLSP server."""

    def __init__(self, stop_on_exit: bool = True, *, register_signal_handlers: bool = True):
        """Configure cleanup of the language-server subprocess.

        Args:
            stop_on_exit: Stop the server when Python exits normally.
            register_signal_handlers: Install SIGINT and SIGTERM handlers that stop
                the server. This replaces the application's existing handlers;
                disable it to preserve them.
        """
        self.port = None
        # Keep the supervisor unreaped until the provider has cleaned up its group.
        self.server_process = None
        self._lifetime_connection: socket.socket | None = None
        self._stopping = False
        if stop_on_exit:
            atexit.register(self.stop)
        if register_signal_handlers:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)

    def _find_free_port(self):
        """Find a free port for the PyLSP server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", 0))
            self.port = s.getsockname()[1]
        return self.port

    def start(self):
        """Start the PyLSP server."""
        if self.is_running():
            return
        if self.port is None:
            self._find_free_port()

        logger.info(f"Starting PyLSP server on port {self.port}")
        host_connection, supervisor_connection = socket.socketpair()
        supervisor_fd = supervisor_connection.fileno()
        launcher = Path(__file__).with_name("_pylsp_launcher.py")
        self._lifetime_connection = host_connection
        try:
            self.server_process = subprocess.Popen(
                [
                    sys.executable,
                    str(launcher),
                    str(supervisor_fd),
                    str(os.getpid()),
                    "--ws",
                    "--port",
                    str(self.port),
                ],
                pass_fds=(supervisor_fd,),
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except BaseException:
            self._lifetime_connection = None
            host_connection.close()
            raise
        finally:
            supervisor_connection.close()

    def _supervisor_exited(self, timeout_ms: int) -> bool:
        connection = self._lifetime_connection
        fd = connection.fileno() if connection is not None else -1
        if fd < 0:
            return True
        poller = select.poll()
        poller.register(fd, select.POLLIN)
        return bool(poller.poll(timeout_ms))

    def _stop_supervisor(self, *, graceful: bool) -> None:
        if self._stopping:
            return

        self._stopping = True
        try:
            process = self.server_process
            if process is None:
                return
            if graceful:
                # EOF is the supervisor's shutdown request. Keep the read side
                # open so we can wait for the supervisor before reaping it.
                try:
                    self._lifetime_connection.shutdown(socket.SHUT_WR)
                except OSError:
                    if not self._supervisor_exited(0):
                        raise
                self._supervisor_exited(_STOP_TIMEOUT * 1000)

            # Signal the group before waiting, while the unreaped supervisor still
            # reserves its PID. A dead supervisor may have left pylsp in the group.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                # macOS can report EPERM for a group with only the dead supervisor.
                if not self._supervisor_exited(0):
                    raise
            process.wait(timeout=_STOP_TIMEOUT)
            self._lifetime_connection.close()
            self._lifetime_connection = None
            self.server_process = None
            # Existing editors reconnect to this port after an unexpected exit.
            if graceful:
                self.port = None
        finally:
            self._stopping = False

    def stop(self):
        """Stop and reap the PyLSP server."""
        self._stop_supervisor(graceful=True)

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        self.stop()

    def is_running(self):
        """Check if the PyLSP server is running."""
        if self.server_process is None:
            return False
        if self._stopping or not self._supervisor_exited(0):
            return True
        self._stop_supervisor(graceful=False)
        return False


stop_on_exit = os.getenv("PYLSP_STOP_ON_EXIT", "1") == "1"
register_signal_handlers = os.getenv("PYLSP_REGISTER_SIGNAL_HANDLERS", "1") == "1"
pylsp_server = PyLSPProvider(
    stop_on_exit=stop_on_exit, register_signal_handlers=register_signal_handlers
)
