import json
from typing import Literal

from qtpy.QtCore import QObject, Signal, Slot


class Connector(QObject):
    javascript_data_sent = Signal(str, str)
    javascript_data_received = Signal(str, str)

    """
    A base class for connecting Python and JavaScript.
    This class provides a mechanism to send and receive data between Python and JavaScript.
    It uses Qt's signal-slot mechanism to handle communication.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._initialized = False
        self._buffer = []

    def _process_startup_buffer(self):
        """
        Process the buffer of data that was sent before the bridge was initialized.
        This is useful for sending initial data to the JavaScript side.
        """
        for name, value in self._buffer:
            self.send(name, value)
        self._buffer.clear()

        # Update the local buffer by reading the current state
        # This is mostly to ensure that we are in sync with the JS side
        self.send("read", "")

    def send(self, name, value):
        """
        Send data to the JavaScript side.
        Args:
            name (str): The name of the data to send.
            value (any): The value to send, which will be serialized to JSON.
        """
        if not self._initialized:
            self._buffer.append((name, value))
            return
        data = json.dumps(value)
        self.javascript_data_sent.emit(name, data)

    @Slot(str, str)
    def _receive(self, name: str, value: str):
        """
        Receive data from the JavaScript side.
        This method is called when the JavaScript side sends data to the Python side.
        Args:


        """
        self.javascript_data_received.emit(name, value)

    def set_initialized(self):
        """
        Set the initialized state of the connector.
        This method is used to indicate that the connector is ready to send and receive data.
        Args:
            value (bool): The new initialized state.
        """
        self._initialized = True
        self._process_startup_buffer()


class EditorBridge(QObject):
    text_changed = Signal()
    language_changed = Signal()
    theme_changed = Signal()
    initialized = Signal()
    completion = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._connector = Connector(parent=self)
        self._connector.javascript_data_received.connect(self.on_new_data_received)
        self._value = ""
        self._language = ""
        self._theme = ""
        self._readonly = False
        self._initialized = False
        self._buffer = []
        self.initialized.connect(self._connector.set_initialized)

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

    @property
    def bridge_initialized(self):
        return self._initialized

    @bridge_initialized.setter
    def bridge_initialized(self, value):
        if self._initialized != value:
            self._initialized = value
            self.initialized.emit()

    def on_value_changed(self, value):
        """Handle value changes from the JavaScript side."""
        self._current_text(value)

    def _current_text(self, value: str):
        if self._value == value:
            return
        self._value = value
        self.text_changed.emit()

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
        self.text_changed.emit()

    def get_language(self):
        return self._language

    def set_language(self, language):
        self._language = language
        self._connector.send("language", language)
        self.language_changed.emit()

    def get_theme(self):
        return self._theme

    def set_theme(self, theme):
        self._theme = theme
        self._connector.send("theme", theme)
        self.theme_changed.emit()

    def set_readonly(self, read_only: bool):
        """Set the editor to read-only mode."""
        self._connector.send("readonly", read_only)
        self._readonly = read_only

    @property
    def value(self):
        return self._value

    @property
    def language(self):
        return self._language

    @property
    def theme(self):
        return self._theme

    def set_host(self, host: str):
        """
        Set the host for the editor.

        Args:
            host (str): The host URL for the editor.
        """
        self._connector.send("lsp_url", host)

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
