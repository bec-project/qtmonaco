import runpy
import signal
from pathlib import Path
from unittest.mock import Mock, call

import pytest

PROVIDER_PATH = Path(__file__).resolve().parents[1] / "qtmonaco" / "pylsp_provider.py"


@pytest.fixture
def provider_module(monkeypatch):
    # Load the provider without importing Qt or registering process-global callbacks.
    monkeypatch.delenv("PYLSP_STOP_ON_EXIT", raising=False)
    monkeypatch.delenv("PYLSP_REGISTER_SIGNAL_HANDLERS", raising=False)
    register_exit = Mock()
    register_signal = Mock()
    monkeypatch.setattr("atexit.register", register_exit)
    monkeypatch.setattr("signal.signal", register_signal)
    namespace = runpy.run_path(str(PROVIDER_PATH))
    return namespace, register_exit, register_signal


def test_default_registers_signal_handlers_and_cleans_up(provider_module):
    namespace, register_exit, register_signal = provider_module
    provider = namespace["pylsp_server"]
    assert register_signal.call_args_list == [
        call(signal.SIGINT, provider._handle_signal),
        call(signal.SIGTERM, provider._handle_signal),
    ]
    register_exit.assert_called_once_with(provider.stop)

    process = Mock()
    provider.server_process = process
    provider.port = 12345
    register_exit.call_args.args[0]()
    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=5)
    assert provider.server_process is None
    assert provider.port is None


@pytest.mark.parametrize("stop_on_exit", [False, True])
@pytest.mark.parametrize("register_signal_handlers", [False, True])
def test_cleanup_and_signal_registration_are_independent(
    provider_module, stop_on_exit, register_signal_handlers
):
    namespace, register_exit, register_signal = provider_module
    register_exit.reset_mock()
    register_signal.reset_mock()
    provider = namespace["PyLSPProvider"](
        stop_on_exit=stop_on_exit, register_signal_handlers=register_signal_handlers
    )

    if stop_on_exit:
        register_exit.assert_called_once_with(provider.stop)
    else:
        register_exit.assert_not_called()
    if register_signal_handlers:
        assert register_signal.call_args_list == [
            call(signal.SIGINT, provider._handle_signal),
            call(signal.SIGTERM, provider._handle_signal),
        ]
        process = Mock()
        provider.server_process = process
        register_signal.call_args_list[0].args[1](signal.SIGINT, None)
        process.terminate.assert_called_once_with()
    else:
        register_signal.assert_not_called()


@pytest.mark.parametrize("stop_on_exit", ["0", "1"])
@pytest.mark.parametrize("register_signal_handlers", ["0", "1"])
def test_singleton_environment_configuration(
    provider_module, monkeypatch, stop_on_exit, register_signal_handlers
):
    _, register_exit, register_signal = provider_module
    register_exit.reset_mock()
    register_signal.reset_mock()
    monkeypatch.setenv("PYLSP_STOP_ON_EXIT", stop_on_exit)
    monkeypatch.setenv("PYLSP_REGISTER_SIGNAL_HANDLERS", register_signal_handlers)
    namespace = runpy.run_path(str(PROVIDER_PATH))
    provider = namespace["pylsp_server"]

    if stop_on_exit == "1":
        register_exit.assert_called_once_with(provider.stop)
    else:
        register_exit.assert_not_called()
    if register_signal_handlers == "1":
        assert register_signal.call_args_list == [
            call(signal.SIGINT, provider._handle_signal),
            call(signal.SIGTERM, provider._handle_signal),
        ]
    else:
        register_signal.assert_not_called()
