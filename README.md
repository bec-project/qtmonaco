# QTMonaco

A Python library that embeds the Monaco Editor (the editor that powers VS Code) into Qt applications using PySide6/PyQt.

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
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
import qtmonaco

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monaco Editor Example")
        self.resize(800, 600)
        
        # Create Monaco editor widget
        self.monaco = qtmonaco.Monaco()
        self.setCentralWidget(self.monaco)
        
        # Set some sample code
        self.monaco.set_text('''
def hello_world():
    print("Hello from Monaco Editor!")
    return "success"

if __name__ == "__main__":
    hello_world()
        ''')
        
        # Set language mode
        self.monaco.set_language("python")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
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
monaco.insert_text(text: str, position: int = None)

# Language and syntax
monaco.set_language(language: str)
monaco.get_language() -> str

# Editor configuration
monaco.set_theme(theme: str)  # "vs", "vs-dark", "hc-black"
monaco.set_font_size(size: int)
monaco.set_word_wrap(enabled: bool)
```

#### Language Server Protocol
```python
# Enable LSP for a language
monaco.enable_language_server(language: str, server_config: dict = None)

# Custom LSP server configuration
monaco.configure_lsp_server("python", {
    "command": ["pylsp"],
    "args": ["--log-level", "debug"],
    "initialization_options": {
        "plugins": {
            "pycodestyle": {"enabled": False},
            "pylint": {"enabled": True}
        }
    }
})
```

#### Signals
```python
# Text change events
monaco.text_changed.connect(on_text_changed)

# Cursor position changes
monaco.cursor_changed.connect(on_cursor_changed)

# Selection changes
monaco.selection_changed.connect(on_selection_changed)
```


### Integration with Qt Applications
```python
class CodeEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["python", "javascript", "cpp", "html"])
        self.language_combo.currentTextChanged.connect(self.monaco.set_language)
        toolbar.addWidget(QLabel("Language:"))
        toolbar.addWidget(self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["vs", "vs-dark", "hc-black"])
        self.theme_combo.currentTextChanged.connect(self.monaco.set_theme)
        toolbar.addWidget(QLabel("Theme:"))
        toolbar.addWidget(self.theme_combo)
        
        layout.addLayout(toolbar)
        
        # Monaco editor
        self.monaco = qtmonaco.Monaco()
        layout.addWidget(self.monaco)
        
        self.setLayout(layout)
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/bec-project/qtmonaco.git
cd qtmonaco

# Install development dependencies
pip install -e ./qtmonaco[dev]

# Install JavaScript dependencies
npm install

# Build the Monaco editor assets
npm run build

# Generate the Qt resource file
python ./qtmonaco/generate_rcc.py

# Run tests
pytest
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

