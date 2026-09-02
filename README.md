<div align="center">

# ni_sh_a.char-IDE

### Run any language. Anywhere.

**A polyglot execution engine, a standalone IDE, and a one-line embeddable component — in one Apache-2.0 package.**

[![CI](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/actions/workflows/ci.yml/badge.svg)](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nishachar-ide?logo=pypi&logoColor=white&color=3775A9)](https://pypi.org/project/nishachar-ide/)
[![npm](https://img.shields.io/npm/v/@nishachar/ide?logo=npm&color=CB3837)](https://www.npmjs.com/package/@nishachar/ide)
[![License](https://img.shields.io/badge/license-Apache--2.0-D22128.svg)](LICENSE)
[![Languages](https://img.shields.io/badge/languages-62-7C5CFF)](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/tree/develop/languages)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-24C38E.svg)](CONTRIBUTING.md)

[**Try it live →**](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/) &nbsp;·&nbsp; [Docs](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/docs/) &nbsp;·&nbsp; [Add a language](CONTRIBUTING.md#add-a-language-in-8-lines) &nbsp;·&nbsp; [Roadmap](ROADMAP.md)

</div>

---

```bash
pip install nishachar-ide && nishachar
```

That opens a full IDE in your browser that runs **62 languages** — Python, Rust, Go, C++, Haskell, COBOL, Brainfuck and [SHE](https://github.com/ni-sh-a-char/SHE) — plus a real terminal for the system commands your code needs.

Or drop it into any web page, in one line:

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/@nishachar/ide"></script>
<nishachar-ide language="she"></nishachar-ide>
```

That snippet has **no backend**. It executes in the visitor's browser tab.

---

## Why this exists

Every online IDE has the same architecture: your code is POSTed to somebody's server, run in somebody's container, and billed to somebody's credit card. That works right up until the free tier ends or the project is abandoned.

ni_sh_a.char-IDE inverts it. **Code always runs on hardware that is already paid for** — the visitor's own browser, or your own machine. There is no central runner to abuse, meter, or shut down. The hosted demo costs its maintainer exactly nothing, and always will.

## Three ways to run code

| Tier | Where it runs | Languages | Setup |
|:--|:--|:--|:--|
| **Browser** | the visitor's tab, via WebAssembly | Python, SHE, JavaScript, TypeScript | none — it's a `<script>` tag |
| **Local** | your machine, your toolchains | anything you have installed | `pip install nishachar-ide` |
| **Docker** | a locked-down container | all 62, safely | Docker running |

One interface covers all three, and `auto` picks per language: your installed toolchain when you have it, a container when you don't.

## Use it three ways

**As an IDE**

```bash
nishachar                      # the full IDE, in your browser
nishachar run hello.she        # language inferred from the extension
nishachar run -l rust -c 'fn main(){println!("hi")}'
nishachar languages            # what's available, and what's installed
```

**As an embeddable component** — a native Web Component, so it works unmodified in React, Vue, Svelte, Angular, Astro, plain HTML, Electron and Tauri:

```html
<nishachar-ide
  language="python"
  theme="dark"
  endpoint="http://localhost:8777"><!-- omit endpoint to run in-browser -->
</nishachar-ide>
```

```js
document.querySelector('nishachar-ide')
  .addEventListener('result', e => console.log(e.detail.stdout));
```

**As a Python library**

```python
import nishachar

result = nishachar.run('say "Hello from SHE!"', "she")
print(result.stdout, result.exit_code, result.duration_ms)

nishachar.run_file("script.rs", runner="docker", timeout=30)
```

## A language is data, not code

No language has an integration written for it. Every one is a single JSON file:

```json
{
  "id": "python",
  "name": "Python",
  "extensions": [".py"],
  "image": "python:3.12-slim",
  "run": ["python", "{file}"],
  "template": "print(\"Hello!\")\n"
}
```

That is the whole integration. **Adding a language is an 8-line pull request that touches no source code** — and it is the best first contribution this project has to offer. [Start here.](CONTRIBUTING.md#add-a-language-in-8-lines)

<details>
<summary><b>All 62 languages</b></summary>

Ada · Assembly (NASM) · AWK · Bash · Brainfuck · Bun · C · C# · C++ · Clojure · COBOL · CoffeeScript · Common Lisp · Crystal · D · Dart · Deno · Elixir · Elm · Erlang · F# · Fish · Fortran · Gleam · Go · Groovy · Haskell · Haxe · Io · Java · JavaScript · Julia · Kotlin · Lua · Nim · Nushell · Objective-C · OCaml · Pascal · Perl · PHP · PowerShell · Prolog · Python · R · Racket · Raku · Ruby · Rust · Scala · Scheme · **SHE** · Solidity · SQL (SQLite) · Swift · Tcl · TypeScript · V · Vala · Wren · Zig · Zsh

</details>

## Security

Executing arbitrary code *is* this project's job, so the boundaries are drawn explicitly rather than waved away:

- **Docker tier** — no network, read-only root filesystem, all capabilities dropped, `no-new-privileges`, and hard memory/CPU/process caps. Packages a language needs are installed at *image build* time, so the network is gone by the time your code runs.
- **Local tier** — runs as you, with no isolation. That is correct for your own code and wrong for anyone else's, and the docs say so plainly.
- **Every tier** — wall-clock timeout, output byte cap, and a full process-tree kill on timeout.
- **The server** — refuses to serve the unsandboxed runner on a non-loopback address, validates the `Host` header against DNS rebinding, and ships with CORS closed and the terminal disabled.

Read [SECURITY.md](SECURITY.md) for the full model, including what it does *not* protect against.

## Contributing

> **Where's the code?** This branch (`main`) holds the website and the community
> documents. All source lives on **[`develop`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/tree/develop)** —
> branch from there, and target your pull requests there.

Good first issues are labelled [`good first issue`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/labels/good%20first%20issue), and the easiest of them is adding your favourite language. See [CONTRIBUTING.md](CONTRIBUTING.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## License

[Apache License 2.0](LICENSE) — commercial use, modification and distribution permitted, with an explicit patent grant.

<div align="center"><sub>Built by <a href="https://github.com/PIYUSH-MISHRA-00">Piyush Mishra</a> · If this is useful, a ⭐ helps others find it.</sub></div>
