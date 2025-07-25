import json
from typing import Literal

from qtpy.QtCore import Signal
from qtpy.QtWebChannel import QWebChannel
from qtpy.QtWebEngineWidgets import QWebEngineView

from qtmonaco.connector import Connector
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
    text_changed = Signal(str)
    language_changed = Signal(str)
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pylsp_host = get_pylsp_host()
        self._connector = Connector(parent=self)
        self._value = ""
        self._language = ""
        self._theme = ""
        self._readonly = False
        self._current_cursor = {"line": 1, "column": 1}
        self._initialized = False
        self._lsp_header = ""
        self._buffer = []

        page = MonacoPage(parent=self)
        self.setPage(page)

        self._channel = QWebChannel(self)
        self.page().setWebChannel(self._channel)
        self._channel.registerObject("connector", self._connector)
        self._connector.javascript_data_received.connect(self.on_new_data_received)

        self.initialized.connect(lambda: self._set_host(self.pylsp_host))
        self._load_editor()

    @property
    def bridge_initialized(self):
        return self._initialized

    @bridge_initialized.setter
    def bridge_initialized(self, value):
        if self._initialized != value:
            self._initialized = value
            self.initialized.emit()

    def _load_editor(self):
        """Load the Monaco Editor HTML content."""
        raw_html = get_monaco_html()
        base_url = get_monaco_base_url()
        self.setHtml(raw_html, base_url)

    def _set_host(self, host: str):
        """
        Set the LSP host once the bridge is initialized.

        Args:
            host (str): The host URL for the editor.
        """
        self._connector.send("lsp_url", host)

    def on_new_data_received(self, name: str, value: str):
        """
        Handle new data received from JavaScript.
        This method is called when the JavaScript side sends data to the Python side.
        """
        data = json.loads(value)
        if hasattr(self, name):
            method = getattr(self, name)
            if callable(method):
                method(data)
                return
            if hasattr(self, name):
                setattr(self, name, data)
                return
        else:
            print(f"Warning: No method or property named '{name}' in EditorBridge.")

    def on_value_changed(self, value):
        """Handle value changes from the JavaScript side."""
        self._current_text(value)

    def _current_text(self, value: str):
        if self._value == value:
            return
        self._value = value
        self.text_changed.emit(value)

    ##########################
    ### Public API Methods ###
    ##########################

    def set_text(self, value: str):
        """
        Set the value in the editor.

        Args:
            value (str): The new value to set in the editor.
        """
        if self._value == value:
            return
        if self._readonly:
            raise ValueError("Editor is in read-only mode, cannot set value.")
        if not isinstance(value, str):
            raise TypeError("Value must be a string.")
        self._value = value
        self._connector.send("set_text", value)
        self.text_changed.emit(value)

    def get_text(self):
        """
        Get the current value in the editor.

        Returns:
            str: The current value in the editor.
        """
        return self._value

    def insert_text(self, text: str, line: int | None = None, column: int | None = None):
        """
        Insert text at the current cursor position.

        Args:
            text (str): The text to insert.
        """
        if self._readonly:
            raise ValueError("Editor is in read-only mode, cannot insert text.")
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")
        if line is not None and column is None:
            column = 1  # Default to column 1 if not provided
        elif column is not None and line is None:
            raise ValueError("Column must be provided if line is specified.")
        self._connector.send("insert", {"text": text, "line": line, "column": column})

    def delete_line(self, line: int | None = None):
        """
        Delete a specific line in the editor.

        Args:
            line (int | None): The line number to delete (1-based). If None, deletes the current line.
        """
        if self._readonly:
            raise ValueError("Editor is in read-only mode, cannot delete line.")
        self._connector.send("delete_line", line if line is not None else "current")

    def get_language(self):
        return self._language

    def set_language(self, language):
        self._language = language
        self._connector.send("language", language)
        self.language_changed.emit(language)

    def set_minimap_enabled(self, enabled: bool):
        """
        Enable or disable the minimap in the editor.

        Args:
            enabled (bool): True to enable the minimap, False to disable it.
        """
        self._connector.send("minimap", enabled)

    def get_theme(self):
        return self._theme

    def set_theme(self, theme):
        self._theme = theme
        self._connector.send("theme", theme)
        self.theme_changed.emit(theme)

    def set_readonly(self, read_only: bool):
        """Set the editor to read-only mode."""
        self._connector.send("readonly", read_only)
        self._readonly = read_only

    def set_cursor(
        self,
        line: int,
        column: int = 1,
        move_to_position: Literal[None, "center", "top", "position"] = None,
    ):
        """
        Set the cursor position in the editor.

        Args:
            line (int): Line number (1-based).
            column (int): Column number (1-based), defaults to 1.
            move_to_position (Literal[None, "center", "top", "position"], optional): Position to move the cursor to.
        """
        self._connector.send(
            "set_cursor", {"line": line, "column": column, "moveToPosition": move_to_position}
        )

    @property
    def current_cursor(self):
        return self._current_cursor

    def set_highlighted_lines(self, start_line: int, end_line: int):
        """
        Highlight a range of lines in the editor.

        Args:
            start_line (int): The starting line number (1-based).
            end_line (int): The ending line number (1-based).
        """
        self._connector.send("highlight_lines", {"start": start_line, "end": end_line})

    def clear_highlighted_lines(self):
        """
        Clear any highlighted lines in the editor.
        This method sends a command to the JavaScript side to clear the highlights.
        """
        self._connector.send("remove_highlight", {})

    def set_vim_mode_enabled(self, enabled: bool):
        """
        Enable or disable Vim mode in the editor.

        Args:
            enabled (bool): True to enable Vim mode, False to disable it.
        """
        self._connector.send("vim_mode", enabled)

    def set_lsp_header(self, header: str):
        """
        Set the LSP header to be prepended to the document.
        Args:
            header (str): The header text to prepend.
        """
        if not isinstance(header, str):
            raise TypeError("Header must be a string.")
        header = header.strip()
        if not header.endswith("\n"):
            header += "\n"
        self._lsp_header = header
        self._connector.send("set_lsp_header", header)

    def get_lsp_header(self) -> str:
        """
        Get the current LSP header.
        Returns:
            str: The current LSP header.
        """
        return self._lsp_header


if __name__ == "__main__":
    import logging
    import sys

    from qtpy.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    editor = Monaco()
    editor.set_minimap_enabled(False)
    editor.show()
    sys.exit(app.exec_())
