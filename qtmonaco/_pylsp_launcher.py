"""Run pylsp under a supervisor that watches the host's lifetime connection."""

import os
import select
import signal
import subprocess
import sys
from contextlib import suppress

_GRACEFUL_STOP_TIMEOUT = 2
_POLL_INTERVAL_MS = 200


def main() -> None:
    """Reap pylsp and terminate remaining workers when the session ends."""
    group_id = os.getpid()
    if os.getsid(0) != group_id:
        raise RuntimeError("The pylsp supervisor requires its own session")

    lifetime_fd, host_pid = map(int, sys.argv[1:3])
    os.set_inheritable(lifetime_fd, False)
    poller = select.poll()
    poller.register(lifetime_fd, select.POLLIN)

    if os.getppid() != host_pid or poller.poll(0):
        return

    server = subprocess.Popen([sys.executable, "-m", "pylsp", *sys.argv[3:]])
    try:
        while server.poll() is None:
            # Checking the parent also covers a fork that inherited its connection.
            if os.getppid() != host_pid or poller.poll(_POLL_INTERVAL_MS):
                server.terminate()
                with suppress(subprocess.TimeoutExpired):
                    server.wait(timeout=_GRACEFUL_STOP_TIMEOUT)
                break
    finally:
        try:
            if server.poll() is None:
                server.kill()
                server.wait(timeout=_GRACEFUL_STOP_TIMEOUT)
        finally:
            # Include the supervisor so no workers outlive this session.
            os.killpg(group_id, signal.SIGKILL)


if __name__ == "__main__":
    main()
