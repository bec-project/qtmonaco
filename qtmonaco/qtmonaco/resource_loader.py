import os

from qtpy.QtCore import QFile, QIODevice, QResource, QUrl

import qtmonaco._monaco_rcc  # pylint: disable=unused-import


def load_resource_html(resource_path: str) -> str:
    """Load HTML content from Qt resources."""
    file = QFile(resource_path)
    if file.open(QIODevice.OpenModeFlag.ReadOnly):
        content = file.readAll()
        file.close()
        return content.toStdString()
    else:
        raise FileNotFoundError(f"Resource not found: {resource_path}")


def get_monaco_html():
    """Get Monaco Editor HTML content from Qt resources."""
    return load_resource_html(":/monaco/dist/index.html")


def get_monaco_base_url():
    """Get the base URL for Monaco Editor resources."""
    return QUrl("qrc:/monaco/dist/")
