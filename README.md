# QTMonaco

A Python library that embeds the Monaco Editor (the editor that powers VS Code) into Qt applications using
PySide6/PyQt6.

*Inspired by [monaco-qt](https://github.com/DaelonSuzuka/monaco-qt) by DaelonSuzuka.*

## Features

- 🚀 **Monaco Editor Integration** - Full Monaco Editor with syntax highlighting, tab-completion, and more
- 🔌 **Language Server Protocol Support** - Built-in LSP client for advanced language features
- 🌍 **Cross-Platform** - Works on macOS and Linux.
- 🎨 **Qt Integration** - Seamless integration with Qt applications
- 📦 **Easy Installation** - Available on PyPI with minimal dependencies

## Installation

```bash
pip install qtmonaco
```

## Quick Start

```python
from qtpy.QtWidgets import QApplication
from qtmonaco import Monaco

qapp = QApplication([])
widget = Monaco()
# set the default size
widget.resize(800, 600)
widget.set_language("python")
widget.set_theme("vs-dark")
widget.editor.set_minimap_enabled(False)
widget.set_text(
    """
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bec_lib.devicemanager import DeviceContainer
    from bec_lib.scans import Scans
    dev: DeviceContainer
    scans: Scans

#######################################
########## User Script #####################
#######################################

# This is a comment
def hello_world():
    print("Hello, world!")
            """
)

widget.show()
qapp.exec_()
```

## Features Overview

### Monaco Editor Features
- **Syntax Highlighting** - Support for 80+ programming languages
- **Code Folding** - Collapse and expand code sections
- **Find & Replace** - Advanced search and replace functionality
- **Multiple Cursors** - Edit multiple locations simultaneously
- **Minimap** - Overview of the entire file
- **Command Palette** - Quick access to editor commands

### Language Server Protocol (LSP)
QTMonaco comes with a built-in LSP support for python (pylsp). Extended support is planned. 


### Qt Integration
- **Native Qt Widget** - Works seamlessly with other Qt widgets
- **Signal/Slot Support** - Connect to text changes, cursor movements, etc.
- **Theming** - Integrates with Qt application themes
- **Resource Management** - Efficient handling of editor assets

## API Reference

### Monaco Class

#### Basic Methods
```python
# Text operations
monaco.set_text(content: str)
monaco.get_text() -> str
monaco.set_cursor(line: int, column: int)  # Set cursor position
monaco.current_cursor() -> tuple[int, int]  # Get current cursor position

# Language and syntax
monaco.set_language(language: str)
monaco.get_language() -> str

# Editor configuration
monaco.set_theme(theme: str)  # "vs", "vs-dark", "hc-black"
monaco.get_theme() -> str
monaco.set_read_only(read_only: bool)
monaco.set_minimap_enabled(enabled: bool)

```

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **Monaco Editor**: Licensed under the MIT License
- Other dependencies retain their respective licenses

## Acknowledgments

- **[monaco-qt](https://github.com/DaelonSuzuka/monaco-qt)** - The original project that inspired QTMonaco
- **Monaco Editor** - The amazing editor that powers VS Code
- **Language Server Protocol** - Microsoft's LSP for consistent language support
- **PySide6/PyQt** - Qt bindings for Python
- **Vite** - Fast build tool for modern web development

