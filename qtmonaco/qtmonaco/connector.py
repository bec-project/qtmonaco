import json

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
        if hasattr(parent, "initialized"):
            parent.initialized.connect(self.set_initialized)
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

            name (str): The name of the data being received.
            value (str): The value being received, which is expected to be a JSON string.
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
