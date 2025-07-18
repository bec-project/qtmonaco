import atexit
import logging
import signal
import socket
import subprocess

logger = logging.getLogger(__name__)


class PyLSPProvider:
    """A provider for the PyLSP server."""

    def __init__(self):
        self.port = None
        self.server_process = None
        atexit.register(self.stop)
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
        if self.port is None:
            self._find_free_port()
        # Here you would start the PyLSP server using the found port
        logger.info(f"Starting PyLSP server on port {self.port}")
        self.server_process = subprocess.Popen(
            ["pylsp", "--ws", "--port", str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def stop(self):
        """Stop the PyLSP server."""
        if not self.server_process:
            return

        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
        self.server_process = None
        self.port = None

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        self.stop()

    def is_running(self):
        """Check if the PyLSP server is running."""
        return self.server_process is not None and self.server_process.poll() is None


pylsp_server = PyLSPProvider()
