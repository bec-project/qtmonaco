import logging

from qtpy import PYQT5

if PYQT5:
    from qtpy.QtWebEngineWidgets import QWebEnginePage
else:
    from qtpy.QtWebEngineCore import QWebEnginePage


logger = logging.getLogger(__name__)


def _console_message_level_name(level):
    # PyQt6/PySide6 expose Qt enum values with a Python-style ``name`` attribute.
    name = getattr(level, "name", None)
    if name is not None:
        return name

    # PyQt5 uses older enum wrappers, so compare against the QWebEnginePage constants.
    for level_name in ("InfoMessageLevel", "WarningMessageLevel", "ErrorMessageLevel"):
        if getattr(QWebEnginePage, level_name, None) == level:
            return level_name

    # Keep console logging non-fatal if another Qt binding returns an unexpected value.
    return str(level)


class MonacoPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        level_name = _console_message_level_name(level)
        logger.debug(f"[JS Console] {level_name} at line {line} in {source}: {message}")
