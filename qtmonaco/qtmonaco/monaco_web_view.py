from typing import Literal

from qtpy.QtCore import Signal
from qtpy.QtWebChannel import QWebChannel
from qtpy.QtWebEngineWidgets import QWebEngineView

from qtmonaco.editor_bridge import EditorBridge
from qtmonaco.monaco_page import MonacoPage
from qtmonaco.resource_loader import get_monaco_base_url, get_monaco_html


def get_pylsp_host() -> str:
    """
    Get the host address for the PyLSP server.
    This function initializes the PyLSP server if it is not already running
    and returns the host address in the format 'localhost:port'.
    Returns:
        str: The host address of the PyLSP server.
    """
    # lazy import to only load when needed
    # pylint: disable=import-outside-toplevel
    from qtmonaco.pylsp_provider import pylsp_server

    if not pylsp_server.is_running():
        pylsp_server.start()

    return f"localhost:{pylsp_server.port}"


class Monaco(QWebEngineView):
    initialized = Signal()
    textChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pylsp_host = get_pylsp_host()

        self._setup_page()
        self._setup_bridge()
        self._load_editor()

    def _setup_page(self):
        """Initialize the web engine page."""
        page = MonacoPage(parent=self)
        self.setPage(page)

    def _setup_bridge(self):
        """Initialize the bridge for communication with JavaScript."""
        self._channel = QWebChannel(self)
        self._bridge = EditorBridge()

        self.page().setWebChannel(self._channel)
        self._channel.registerObject("connector", self._bridge._connector)

        self._bridge.initialized.connect(self._set_host)
        self._bridge.initialized.connect(self.initialized)
        self._bridge.text_changed.connect(lambda: self.textChanged.emit(self._bridge.value))

    def _load_editor(self):
        """Load the Monaco Editor HTML content."""
        raw_html = get_monaco_html()
        base_url = get_monaco_base_url()
        self.setHtml(raw_html, base_url)

    def _set_host(self):
        """Set the LSP host once the bridge is initialized."""
        self._bridge.set_host(self.pylsp_host)

    # Public API methods
    def text(self):
        return self._bridge.value

    def set_text(self, text: str):
        self._bridge.set_text(text)

    def set_cursor(
        self,
        line: int,
        column: int = 1,
        move_to_position: Literal[None, "center", "top", "position"] = None,
    ):
        """Set the cursor position in the editor.

        Args:
            line (int): Line number (1-based)
            column (int): Column number (1-based), defaults to 1
        """
        self._bridge.set_cursor(line, column, move_to_position)

    def get_language(self) -> str:
        """Get the current programming language for syntax highlighting in the editor."""
        return self._bridge.get_language()

    def set_language(self, language: str):
        """Set the programming language for syntax highlighting in the editor.

        Args:
            language (str): The programming language to set (e.g., "python", "javascript").
        """
        self._bridge.set_language(language)

    def get_theme(self):
        return self._bridge.get_theme()

    def set_theme(self, theme: str):
        """Set the theme for the Monaco editor.

        Args:
            theme (str): The theme to apply (e.g., "vs", "vs-dark").
        """
        self._bridge.set_theme(theme)

    def set_read_only(self, read_only: bool):
        """Set the editor to read-only mode."""
        self._bridge.set_readonly(read_only)

    def shutdown(self):
        if hasattr(self._bridge, "shutdown"):
            self._bridge.shutdown()


if __name__ == "__main__":
    import logging
    import sys

    from qtpy.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    editor = Monaco()
    editor.show()
    sys.exit(app.exec_())
