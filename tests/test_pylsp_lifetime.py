import os
import runpy
import select
import signal
import socket
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from unittest.mock import Mock, call

import pytest

_HOST_SCRIPT = """
import sys
import time
from qtmonaco.pylsp_provider import PyLSPProvider

provider = PyLSPProvider(stop_on_exit=False, register_signal_handlers=False)
provider.start()
print(provider.server_process.pid, provider.port, flush=True)
command = sys.stdin.readline().strip()
if command == "poll":
    deadline = time.monotonic() + 5
    while provider.is_running():
        assert time.monotonic() < deadline, "Supervisor did not exit"
        time.sleep(0.05)
else:
    provider.stop()
"""


def _connect_to_pylsp(port: int) -> socket.socket:
    deadline = time.monotonic() + 10
    while True:
        try:
            return socket.create_connection(("127.0.0.1", port), timeout=5)
        except ConnectionRefusedError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)


def _assert_connection_closed(connection: socket.socket) -> None:
    with suppress(ConnectionResetError):
        assert connection.recv(1) == b"", "pylsp kept its connection open"


def _install_pylsp_with_worker(path: Path) -> None:
    package = path / "pylsp"
    package.mkdir()
    (package / "__init__.py").touch()
    worker = """
import socket
import sys

with socket.create_server(("127.0.0.1", int(sys.argv[1]))) as listener:
    connection, _ = listener.accept()
    with connection:
        connection.recv(1)
"""
    (package / "__main__.py").write_text(
        f"""
import subprocess
import sys
import time

subprocess.Popen([sys.executable, "-c", {worker!r}, sys.argv[-1]])
time.sleep(30)
""",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "shutdown",
    [
        "host-killed",
        "host-group-killed",
        "provider-stop",
        "supervisor-stopped",
        "supervisor-killed-stop",
        "supervisor-killed-poll",
    ],
)
def test_pylsp_exits_on_shutdown(shutdown, tmp_path):
    env = None
    if shutdown == "host-group-killed":
        _install_pylsp_with_worker(tmp_path)
        env = {**os.environ, "PYTHONPATH": str(tmp_path)}

    supervisor_pid = None
    with subprocess.Popen(
        [sys.executable, "-c", _HOST_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env=env,
    ) as host:
        try:
            assert select.select([host.stdout], [], [], 10)[0], "Host did not report the pylsp port"
            supervisor_pid, port = map(int, host.stdout.readline().split())

            # Observe the server without sending an LSP initialize request.
            with _connect_to_pylsp(port) as connection:
                if shutdown == "host-killed":
                    host.kill()
                elif shutdown == "host-group-killed":
                    os.killpg(host.pid, signal.SIGKILL)
                else:
                    if shutdown == "supervisor-stopped":
                        os.kill(supervisor_pid, signal.SIGSTOP)
                    if shutdown.startswith("supervisor-killed-"):
                        os.kill(supervisor_pid, signal.SIGKILL)
                    command = "poll" if shutdown == "supervisor-killed-poll" else "stop"
                    host.stdin.write(f"{command}\n")
                    host.stdin.flush()
                assert host.wait(timeout=10) == (
                    -signal.SIGKILL if shutdown in {"host-killed", "host-group-killed"} else 0
                )
                _assert_connection_closed(connection)
            supervisor_pid = None
        finally:
            if host.poll() is None:
                host.kill()
                host.wait(timeout=5)
            if supervisor_pid is not None:
                with suppress(ProcessLookupError):
                    os.killpg(supervisor_pid, signal.SIGKILL)


def test_supervisor_stops_pylsp_while_gil_is_held(tmp_path):
    pylsp = tmp_path / "pylsp"
    pylsp.mkdir()
    (pylsp / "__init__.py").touch()
    (pylsp / "__main__.py").write_text(
        "import ctypes\n"
        "import signal\n"
        "def main():\n"
        "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "    print('ready', flush=True)\n"
        "    ctypes.PyDLL(None).sleep(30)\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    launcher = Path(__file__).resolve().parents[1] / "qtmonaco" / "_pylsp_launcher.py"
    read_fd, write_fd = os.pipe()
    try:
        with subprocess.Popen(
            [sys.executable, str(launcher), str(read_fd), str(os.getpid())],
            pass_fds=(read_fd,),
            start_new_session=True,
            stdout=subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": str(tmp_path)},
        ) as supervisor:
            try:
                assert select.select([supervisor.stdout], [], [], 5)[0]
                assert supervisor.stdout.readline() == b"ready\n"
                time.sleep(0.1)  # Let the stand-in enter the native call.
                os.close(write_fd)
                write_fd = None
                assert supervisor.wait(timeout=5) == -signal.SIGKILL
            finally:
                if supervisor.poll() is None:
                    os.killpg(supervisor.pid, signal.SIGKILL)
    finally:
        os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("PYLSP_STOP_ON_EXIT", "0")
    monkeypatch.setenv("PYLSP_REGISTER_SIGNAL_HANDLERS", "0")
    source = Path(__file__).resolve().parents[1] / "qtmonaco" / "pylsp_provider.py"
    return runpy.run_path(str(source))["pylsp_server"]


def test_stop_signals_group_before_reaping_supervisor(provider, monkeypatch):
    signals_and_wait = Mock()
    monkeypatch.setattr(os, "killpg", signals_and_wait.killpg)
    process = Mock(pid=12345, wait=signals_and_wait.wait)
    provider.server_process = process
    provider.port = 12345

    connection, peer = socket.socketpair()
    with connection, peer:
        provider._lifetime_connection = connection
        peer.settimeout(1)

        def wait_for_supervisor(timeout_ms):
            assert timeout_ms == 5000
            assert peer.recv(1) == b""
            return False

        monkeypatch.setattr(provider, "_supervisor_exited", wait_for_supervisor)
        provider.stop()
        provider.stop()

        assert signals_and_wait.mock_calls == [
            call.killpg(process.pid, signal.SIGKILL),
            call.wait(timeout=5),
        ]
        assert provider.server_process is None
        assert provider.port is None
        assert connection.fileno() == -1


def test_stop_without_supervisor_keeps_reserved_port(provider):
    provider.port = 12345

    provider.stop()

    assert provider.port == 12345


def test_polling_closes_connection_after_supervisor_exit(provider, monkeypatch):
    monkeypatch.setattr(os, "killpg", Mock())
    provider.server_process = Mock(pid=12345)
    connection, peer = socket.socketpair()
    peer.close()
    with connection:
        provider._lifetime_connection = connection
        assert not provider.is_running()
        assert connection.fileno() == -1


def test_pylsp_restarts_on_original_port_after_supervisor_exit(provider):
    provider.start()
    port = provider.port
    try:
        with _connect_to_pylsp(port) as connection:
            os.kill(provider.server_process.pid, signal.SIGKILL)
            deadline = time.monotonic() + 5
            while provider.is_running():
                assert time.monotonic() < deadline, "Supervisor did not exit"
                time.sleep(0.05)
            _assert_connection_closed(connection)

        provider.start()
        assert provider.port == port
        with _connect_to_pylsp(port):
            pass
    finally:
        provider.stop()
