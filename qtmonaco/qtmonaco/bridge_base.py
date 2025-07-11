import json

from qtpy.QtCore import QObject, Signal, Slot


class BaseBridge(QObject):
    initialized = Signal()
    sendDataChanged = Signal(str, str)
    completion = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._initialized = False
        self._buffer = []
        self.initialized.connect(self._process_startup_buffer)

    def _process_startup_buffer(self):
        """
        Process the buffer of data that was sent before the bridge was initialized.
        This is useful for sending initial data to the JavaScript side.
        """
        for name, value in self._buffer:
            self._send_to_js(name, value)
        self._buffer.clear()

        # Update the local buffer by reading the current state
        # This is mostly to ensure that we are in sync with the JS side
        self._send_to_js("read", "")

    def _send_to_js(self, name, value):
        if not self._initialized:
            self._buffer.append((name, value))
            return
        data = json.dumps(value)
        self.sendDataChanged.emit(name, data)

    @Slot(str, str)
    def receive_from_js(self, name, value):
        data = json.loads(value)

        if name == "bridge_initialized":
            self._initialized = data
            self.initialized.emit()
            return
        if name == "setValue":
            self.on_value_changed(data)
            return
        print(f"Received from JS: {name} = {data}")
        self.setProperty(name, data)

    @property
    def bridge_initialized(self):
        return self._initialized

    @bridge_initialized.setter
    def bridge_initialized(self, value):
        if self._initialized != value:
            self._initialized = value
            self.initialized.emit()

    def on_value_changed(self, value):
        """
        Placeholder method to handle value changes.
        This can be overridden in subclasses to implement specific behavior.
        """
