import logging

from qtpy import PYQT5

if PYQT5:
    from qtpy.QtWebEngineWidgets import QWebEnginePage
else:
    from qtpy.QtWebEngineCore import QWebEnginePage


logger = logging.getLogger(__name__)


class MonacoPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        logger.debug(f"[JS Console] {level.name} at line {line} in {source}: {message}")
