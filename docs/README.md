# ni_sh_a.char‑IDE  
**A simple IDE to execute Python code**

`ni_sh_a.char-IDE` (pronounced “nish‑a‑char‑IDE”) is a lightweight, cross‑platform Integrated Development Environment built with Python and Qt. It provides a clean editor, a built‑in console, and one‑click execution of scripts. The project is deliberately minimal – perfect for teaching, quick prototyping, or anyone who wants a no‑frills Python editor.

---

## Table of Contents
- [Features](#features)  
- [Installation](#installation)  
  - [From PyPI (recommended)](#from-pypi-recommended)  
  - [From source](#from-source)  
- [Quick Start](#quick-start)  
- [Usage](#usage)  
  - [Command‑line interface](#command-line-interface)  
  - [Graphical user interface](#graphical-user-interface)  
- [API Documentation](#api-documentation)  
  - [Core classes](#core-classes)  
  - [Utility functions](#utility-functions)  
- [Examples](#examples)  
  - [Running a script from the CLI](#running-a-script-from-the-cli)  
  - [Embedding the editor in another app](#embedding-the-editor-in-another-app)  
- [Configuration & Customisation](#configuration--customisation)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features
| Feature | Description |
|---------|-------------|
| **Syntax‑highlighted editor** | Powered by **QScintilla** (or **Qt‑TextEdit** fallback). |
| **Integrated console** | Executes code in a separate subprocess, captures stdout/stderr, and displays results in real time. |
| **One‑click run** | `F5` (or the toolbar button) runs the current file. |
| **Project management** | Open a folder, browse files, and keep multiple tabs. |
| **Cross‑platform** | Works on Windows, macOS, and Linux. |
| **Extensible API** | Use the `char_ide` package programmatically (e.g., embed the editor in your own Qt app). |
| **Lightweight** | No heavyweight dependencies – just Python 3.8+ and Qt. |

---

## Installation

### From PyPI (recommended)

```bash
# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# Install the package
pip install ni_sh_a.char-IDE
```

The command above installs:

* `char_ide` – the Python package (core API)  
* `char_ide_gui` – the Qt‑based desktop application (`char-ide` entry point)  

### From source

If you want the latest development version or need to modify the code:

```bash
# Clone the repository
git clone https://github.com/your‑org/ni_sh_a.char-IDE.git
cd ni_sh_a.char-IDE

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e .[dev]
```

**Development dependencies** (included in the `dev` extra)  

| Package | Reason |
|---------|--------|
| `PyQt6` or `PySide6` | GUI toolkit |
| `QScintilla` | Advanced code editing (syntax highlighting, line numbers) |
| `pytest` | Test suite |
| `sphinx` | Documentation generation |
| `black`, `ruff` | Code formatting & linting |

> **Tip:** If you only need the GUI and not the optional `QScintilla` features, the fallback editor works out‑of‑the‑box with just `PyQt6`/`PySide6`.

---

## Quick Start

```bash
# Launch the IDE (installed via pip)
char-ide
```

The main window opens with a blank editor. Use **File → Open** or drag‑and‑drop a `.py` file to start editing. Press **F5** (or click the ▶️ Run button) to execute the script; output appears in the bottom console pane.

---

## Usage

### Command‑line Interface

`char-ide` ships with a small CLI wrapper that can be used in scripts or from the terminal.

```bash
# Run a script directly (no GUI)
char-ide run path/to/script.py

# Open the GUI with a specific file pre‑loaded
char-ide open path/to/script.py
```

#### CLI Options

| Option | Alias | Description |
|--------|-------|-------------|
| `--run`, `-r` | | Execute the given file and exit (non‑interactive). |
| `--open`, `-o` | | Open the GUI with the file loaded. |
| `--project`, `-p` | | Open a folder as a project (shows file tree). |
| `--no-console` | | Hide the integrated console on start‑up. |
| `--theme <name>` | | Choose a built‑in theme (`light`, `dark`). |
| `--help`, `-h` | | Show help. |

### Graphical User Interface

| Area | Description |
|------|-------------|
| **Menu Bar** | File, Edit, View, Run, Help. |
| **Toolbar** | New, Open, Save, Run (▶️), Stop (⏹), Theme selector. |
| **Editor Pane** | Tabbed code editors with line numbers, auto‑indent, and syntax highlighting. |
| **Console Pane** | Real‑time stdout/stderr, input support, clear button. |
| **Project Explorer** (optional) | Left‑hand tree view of the opened folder. |
| **Status Bar** | Shows cursor position, file encoding, and execution time. |

#### Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` / `Cmd+N` | New file |
| `Ctrl+O` / `Cmd+O` | Open file |
| `Ctrl+S` / `Cmd+S` | Save |
| `Ctrl+Shift+S` / `Cmd+Shift+S` | Save As |
| `F5` | Run current file |
| `Shift+F5` | Stop running script |
| `Ctrl+/**` | Toggle comment on selected lines |
| `Ctrl+P` / `Cmd+P` | Quick file picker |
| `Ctrl+Q` / `Cmd+Q` | Quit |

---

## API Documentation

`ni_sh_a.char-IDE` can be used as a library. The public API lives in the `char_ide` package.

### Core classes

| Class | Import path | Purpose |
|-------|-------------|---------|
| `IDEApplication` | `char_ide.app` | Subclass of `QApplication` that sets up the main window, theme handling, and global shortcuts. |
| `MainWindow` | `char_ide.gui` | The top‑level Qt `QMainWindow` containing the editor, console, and project explorer. |
| `EditorWidget` | `char_ide.editor` | A `QScintilla`‑based widget (fallback to `QPlainTextEdit`). Provides `load_file()`, `save_file()`, `run_current_file()`. |
| `ConsoleWidget` | `char_ide.console` | Captures subprocess output, supports input via `write()` and `readline()`. |
| `Runner` | `char_ide.runner` | Handles execution of a Python script in a separate process, streams output to `ConsoleWidget`. |
| `ProjectModel` | `char_ide.project` | `QFileSystemModel` wrapper that filters for Python files and provides a tree view. |

#### Example – launching the GUI programmatically

```python
from char_ide.app import IDEApplication
from char_ide.gui import MainWindow

def launch():
    app = IDEApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch()
```

### Utility functions

| Function | Module | Description |
|----------|--------|-------------|
| `run_file(path: str, cwd: Optional[str] = None) -> subprocess.CompletedProcess` | `char_ide.runner` | Synchronously run a script and return the completed process (captures stdout/stderr). |
| `set_theme(name: str)` | `char_ide.themes` | Switch between built‑in themes (`light`, `dark`, `solarized`). |
| `format_code(source: str) -> str` | `char_ide.formatter` | Auto‑format Python code using **black** (fallback to `auto