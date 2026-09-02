# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-09-02

A complete rewrite. v1 was an 80-line Tkinter window that ran Python files;
v2 is a polyglot execution engine, an embeddable component and a standalone
IDE sharing one codebase.

### Added

- **62-language registry.** Every language is one JSON file in `languages/`,
  validated in CI against a schema. Adding a language requires no source
  changes.
- **Three execution tiers behind one interface.**
  - Tier 0 — in-browser via WebAssembly. Python, SHE and JavaScript run with
    no backend at all.
  - Tier 1 — local subprocess against installed toolchains.
  - Tier 2 — sandboxed Docker containers with no network, a read-only root
    filesystem, all capabilities dropped, and memory/CPU/pid caps.
  - `AutoRunner` picks per language: local toolchain when present, container
    otherwise.
- **First-class [SHE](https://github.com/ni-sh-a-char/SHE) support**, including
  in the browser — `she-lang` is installed from PyPI by Pyodide's micropip at
  runtime, and SHE's own CLI entry point is invoked, so browser behaviour
  matches `she run file.she`.
- **`<nishachar-ide>` web component** (npm `@nishachar/ide`) — a native custom
  element with Shadow DOM that works unmodified in React, Vue, Svelte, Angular,
  Astro, plain HTML, Electron and Tauri. Themeable via custom properties and
  `::part()`.
- **Dart and Flutter client** (pub.dev `nishachar_ide`) — typed `NishacharClient`
  with the registry compiled in, so language lookup works offline. One
  dependency.
- **Kotlin, Java and Android client** (Maven Central
  `io.github.ni-sh-a-char:nishachar-ide`) — **zero runtime dependencies**;
  HTTP from `java.net.http` and a small internal JSON reader, so consumers get
  no transitive version conflicts. `@JvmStatic`/`@JvmOverloads` throughout for
  natural Java interop.
- **One registry, five languages.** `tools/generate_bindings.py` generates the
  Dart and Kotlin registries from `languages/*.json`; CI regenerates and diffs,
  so adding a language can never leave a client behind.
- **`nishachar` CLI** — `nishachar` launches the IDE in a browser;
  `nishachar run FILE` infers the language from the extension;
  `nishachar languages` lists what is available and what is installed.
- **HTTP + WebSocket API** — `GET /api/health`, `GET /api/languages`,
  `POST /api/run`, `WS /api/pty`.
- **Interactive terminal** with a real TTY (POSIX `pty`, ConPTY on Windows via
  optional `pywinpty`, pipe fallback elsewhere), so code can drive system
  commands. Off by default; requires `--allow-shell`.
- **Python library API** — `nishachar.run()`, `nishachar.run_file()`,
  `nishachar.languages()`.
- Hand-written CodeMirror 6 theme and a SHE syntax mode.
- Documentation: `ARCHITECTURE.md`, `SECURITY.md`, `CONTRIBUTING.md`,
  `ROADMAP.md`, `languages/README.md`, embedding guide.
- 157 tests across Python, Dart and Kotlin, covering registry resolution,
  timeout enforcement, output capping, Docker argument construction, JSON
  parsing, and every server trust boundary.

### Security

- Unsandboxed execution is refused on non-loopback addresses unless explicitly
  overridden.
- CORS is closed by default; embedding origins are opt-in.
- `Host` header validation on loopback binds blocks DNS rebinding.
- Every tier enforces a wall-clock timeout and a per-stream output cap, and
  kills the entire process tree on timeout rather than just the direct child.
- The Docker tier widens only its single-use scratch directory, because
  `--cap-drop ALL` also removes root's `CAP_DAC_OVERRIDE` bypass. Handing that
  capability back, or forcing `--user`, would have been the worse trade.
- Request bodies capped at 1 MiB; timeouts capped at 120s.

### Changed

- **Licence changed from MIT to Apache 2.0**, adding an explicit patent grant.
- Output line endings are normalised, so identical programs produce identical
  output on Windows and POSIX.
- Programs are run with a UTF-8 stdio environment. Previously any program
  printing non-ASCII failed outright on Windows, where a piped child defaults
  to the ANSI code page and `print("Hello, 世界")` raised `UnicodeEncodeError`
  before producing a byte.
- Repository layout: `main` holds the website and community documents;
  **all source lives on the `v2.0.0` branch**, with `v1.0.0` preserving the
  original Tkinter IDE.

### Removed

- The Tkinter GUI (`main.py`). Preserved at tag [`v1.0.0`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/releases/tag/v1.0.0).
- `github.sh`, an unrelated git-automation script.
- `docs/README.md`, which documented a `char_ide.core` API, a `char-ide` CLI
  and a PyPI package that never existed.

## [1.0.0] — 2022-07-04

The original single-file Tkinter IDE: open a `.py` file, press Run, read the
output. Preserved as the v1 line.

[2.0.0]: https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/releases/tag/v2.0.0
[1.0.0]: https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/releases/tag/v1.0.0
