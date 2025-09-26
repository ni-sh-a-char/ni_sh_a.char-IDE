# ni_sh_a.char‑IDE  
**A simple IDE to execute Python code**

---

## Table of Contents
1. [Overview](#overview)  
2. [Installation](#installation)  
3. [Quick Start / Usage](#quick-start--usage)  
4. [Command‑Line Interface (CLI)](#command-line-interface-cli)  
5. [API Documentation](#api-documentation)  
6. [Examples](#examples)  
7. [Configuration](#configuration)  
8. [Contributing](#contributing)  
9. [License](#license)  

---

## Overview
`ni_sh_a.char-IDE` is a lightweight, cross‑platform Integrated Development Environment (IDE) designed for rapid prototyping and execution of Python scripts. It provides:

* A clean, syntax‑highlighted editor.
* An integrated console that captures `stdout`, `stderr`, and interactive input.
* Project management (open, save, recent files).
* Extensible plugin system (future‑ready).
* A tiny footprint – no heavyweight dependencies beyond the standard Python distribution.

> **Why use char‑IDE?**  
> If you need a simple, no‑frills environment for quick experiments, teaching, or debugging, char‑IDE boots up in seconds and lets you focus on code rather than configuration.

---

## Installation

### Prerequisites
| Tool | Minimum Version |
|------|-----------------|
| Python | 3.8+ |
| pip | 21.0+ |
| Git (optional) | any |

> **Note:** The IDE runs on Windows, macOS, and Linux. No additional system libraries are required.

### Using `pip` (recommended)

```bash
# Create an isolated environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install the latest release from PyPI
pip install ni_sh_a.char-IDE
```

### Installing from source

```bash
# Clone the repository
git clone https://github.com/your-org/ni_sh_a.char-IDE.git
cd ni_sh_a.char-IDE

# Install in editable mode (useful for development)
pip install -e .
```

### Verify the installation

```bash
char-ide --version
# Expected output: char-IDE 1.2.0
```

---

## Quick Start / Usage

### Launch the IDE

```bash
char-ide
```

A window will appear with a split view:

* **Left pane** – the code editor (supports line numbers, syntax highlighting, and basic auto‑completion).  
* **Right pane** – the interactive console where your script’s output appears.

### Basic workflow

1. **Create a new file** – `File → New` or press <kbd>Ctrl+N</kbd>.  
2. **Write Python code** – e.g.:

   ```python
   def greet(name: str) -> str:
       return f"Hello, {name}!"

   if __name__ == "__main__":
       user = input("Your name: ")
       print(greet(user))
   ```

3. **Run the script** – press <kbd>F5</kbd> or click the **Run** button (green triangle).  
4. **View output** – the console will display prompts, results, and any traceback.

### Keyboard shortcuts

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) |
|--------|--------------------------|------------------|
| New file | <kbd>Ctrl+N</kbd> | <kbd>⌘+N</kbd> |
| Open file | <kbd>Ctrl+O</kbd> | <kbd>⌘+O</kbd> |
| Save | <kbd>Ctrl+S</kbd> | <kbd>⌘+S</kbd> |
| Run script | <kbd>F5</kbd> | <kbd>F5</kbd> |
| Toggle console | <kbd>Ctrl+`</kbd> | <kbd>⌘+`</kbd> |
| Find/Replace | <kbd>Ctrl+F</kbd> | <kbd>⌘+F</kbd> |

---

## Command‑Line Interface (CLI)

`char-ide` ships with a small CLI that can be used in scripts or CI pipelines.

### Run a script directly

```bash
char-ide run path/to/script.py
```

* Executes `script.py` in the same sandbox as the GUI console.
* Returns the script’s exit code.

### Open a project folder

```bash
char-ide open /path/to/project/
```

* Opens the IDE with the folder listed in the **File Explorer** pane (future feature).

### Show help

```bash
char-ide --help
```

```
Usage: char-ide [OPTIONS] COMMAND [ARGS]...

Options:
  --version          Show the version and exit.
  -v, --verbose      Enable verbose logging.
  --help             Show this message and exit.

Commands:
  run      Execute a Python file and stream output to stdout.
  open     Open a directory as a project workspace.
  gui      Launch the graphical IDE (default command).
```

---

## API Documentation

The library can be imported and used programmatically. Below is a high‑level overview of the public API. All classes are defined in `char_ide.core`.

### Core Modules

| Module | Description |
|--------|-------------|
| `char_ide.core.editor` | Provides `Editor` – a thin wrapper around `tkinter.Text` with syntax highlighting. |
| `char_ide.core.console` | Implements `Console` – a pseudo‑terminal that captures `stdout`/`stderr` and forwards `input()` calls. |
| `char_ide.core.runner` | Contains `ScriptRunner` – executes a Python file in an isolated namespace. |
| `char_ide.core.project` | Handles `Project` objects (open/save, recent files list). |
| `char_ide.api` | Public façade exposing `run_file`, `launch_gui`, and `get_version`. |

### Example: Using the API in a script

```python
from char_ide.api import run_file, launch_gui, get_version

# 1️⃣ Print the current version
print("char‑IDE version:", get_version())

# 2️⃣ Run a script programmatically (captures output)
output, error, exit_code = run_file("examples/hello_world.py")
print("STDOUT:", output)
print("STDERR:", error)
print("Exit code:", exit_code)

# 3️⃣ Launch the full GUI from another Python process
launch_gui()   # blocks until the window is closed
```

### Detailed Class Reference

#### `char_ide.core.runner.ScriptRunner`

```python
class ScriptRunner:
    def __init__(self, script_path: str, *, cwd: str | None = None):
        """Create a runner for *script_path*.
        Parameters
        ----------
        script_path: str
            Absolute or relative path to the Python file.
        cwd: str | None
            Working directory for the script (defaults to script's folder).
        """

    def run(self) -> tuple[str, str, int]:
        """Execute the script.
        Returns
        -------
        (stdout, stderr, exit_code)
        """
```

#### `char_ide.core.console.Console`

* `write(text: str) -> None` – Append text to the console view.  
* `flush() -> None` – Required for file‑like compatibility.  
* `input(prompt: str = "") -> str` – Prompt the user and return the typed line.

#### `char_ide.core.editor.Editor`

* `load_file(path: str) -> None` – Populate the editor with a file’s contents.  
* `save_file(path: str) -> None` – Write the current buffer to *path*.  
* `get_text() -> str` – Return the current buffer as a string.

---

## Examples

### 1️⃣ Hello World (GUI)

1. Open the IDE (`char-ide`).  
2. Paste the following code into the editor:

   ```python
   print("Hello, char‑IDE!")
   ```

3. Press <kbd>F5</kbd>.  
4. The console shows:

   ```
   Hello, char‑IDE!
   ```

### 2️⃣ Interactive Prompt

```python
# interactive_demo.py
name = input("Enter your name: ")
print(f"Welcome, {name}!")
```

*Run it*: `F5` → the console will pause for input, you type `Alice`, and see:

```
Enter your name: Alice
Welcome, Alice!
```

### 3️⃣ Using the API in a Jupyter notebook

```python
from char_ide.api import run_file

stdout, stderr, rc = run_file("examples/math_demo.py")
print("Result:", stdout)
```

### 4️⃣ Batch execution from a CI pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11