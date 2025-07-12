import os

from qtpy.QtCore import QUrl


def get_monaco_html():
    """Get Monaco Editor HTML content from Qt resources."""
    with open(
        os.path.join(os.path.dirname(__file__), "js_build/index.html"), "r", encoding="utf-8"
    ) as file:
        return file.read()


def get_monaco_base_url():
    """Get the base URL for Monaco Editor resources."""
    return QUrl.fromLocalFile(
        os.path.join(os.path.dirname(__file__), "js_build/assets")
    )  # Use local file URL for the js_build directory
