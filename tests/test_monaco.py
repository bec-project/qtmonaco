import pytest

from qtmonaco.connector import Connector
from qtmonaco.monaco import Monaco
from qtmonaco.monaco_page import MonacoPage


def run_js_check(editor, qtbot, js_check, result, prefix_check="window.qtmonaco && "):
    """
    Helper function to run a JavaScript check in the Monaco editor.
    Args:
        editor (Monaco): The Monaco editor instance.
        qtbot: The pytest-qt bot instance for handling asynchronous operations.
        js_check (str): The JavaScript code to run.
        result (callable): A callback to handle the result of the JavaScript execution.
    """
    output = None

    def js_callback(res):
        nonlocal output
        output = res

    editor.page().runJavaScript(prefix_check + js_check, js_callback)
    qtbot.wait(100)

    try:
        qtbot.waitUntil(lambda: output == result)
    except Exception as e:
        # Log the error if the check fails
        raise TimeoutError(f"JavaScript check failed: {js_check} with error: {e}") from e

    return output


@pytest.fixture
def monaco_editor(qtbot):
    editor = Monaco()
    qtbot.addWidget(editor)
    qtbot.waitExposed(editor)
    return editor


def test_monaco_initialization(monaco_editor, qtbot):
    """Test that Monaco editor initializes correctly."""
    qtbot.waitUntil(lambda: monaco_editor.bridge_initialized, timeout=5000)
    assert monaco_editor.bridge_initialized is True
    assert isinstance(monaco_editor.page(), MonacoPage)
    assert isinstance(monaco_editor._connector, Connector)


@pytest.fixture
def monaco_initialized(qtbot, monaco_editor):
    """Fixture to ensure Monaco editor is initialized."""
    qtbot.waitUntil(lambda: monaco_editor.bridge_initialized, timeout=5000)
    assert monaco_editor.bridge_initialized is True

    # Ensure the Monaco editor is fully initialized
    run_js_check(monaco_editor, qtbot, "window.qtmonaco.initialized === true", True)
    return monaco_editor


def test_monaco_vim_mode(monaco_initialized, qtbot):
    """Test that Monaco editor can toggle Vim mode."""
    # Wait for the editor to be fully initialized
    editor = monaco_initialized
    # Enable Vim mode
    editor.set_vim_mode_enabled(True)
    qtbot.wait(100)  # Allow time for the change to propagate

    # Check if Vim mode is enabled
    run_js_check(editor, qtbot, "window.qtmonaco.vimMode !== null", True)

    editor.set_vim_mode_enabled(False)
    qtbot.wait(100)  # Allow time for the change to propagate

    # Check if Vim mode is disabled
    run_js_check(editor, qtbot, "window.qtmonaco.vimMode !== null", False)


def test_monaco_readonly(monaco_initialized, qtbot):
    """Test that Monaco editor can toggle readonly mode."""
    editor = monaco_initialized
    # Set the editor to readonly
    editor.set_readonly(True)
    qtbot.wait(100)  # Allow time for the change to propagate

    # Check if the editor is readonly
    run_js_check(
        editor,
        qtbot,
        "window.qtmonaco.editor.getOption(window.qtmonaco.monaco.editor.EditorOption.readOnly)",
        True,
    )

    # Set the editor to editable
    editor.set_readonly(False)
    qtbot.wait(100)  # Allow time for the change to propagate

    # Check if the editor is editable
    run_js_check(
        editor,
        qtbot,
        "window.qtmonaco.editor.getOption(window.qtmonaco.monaco.editor.EditorOption.readOnly)",
        False,
    )
