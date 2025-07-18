import logging

from qtpy.QtWebEngineCore import QWebEnginePage

logger = logging.getLogger(__name__)


class MonacoPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        logger.debug(f"[JS Console] {level.name} at line {line} in {source}: {message}")
