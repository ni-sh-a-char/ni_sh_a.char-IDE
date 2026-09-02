# Architecture

How the pieces fit, and why they are shaped this way.

## The constraint that decided everything

This project is maintained on a budget of zero.

The obvious architecture for an online IDE is a hosted runner: the browser
POSTs code to a server, a container executes it, the output comes back. Every
commercial playground works this way. It is also the one thing a $0 project
must not build — an open "run this code" endpoint is a free botnet, and the
bill arrives within days.

So the design inverts it. **Execution happens on hardware someone is already
paying for**: the visitor's browser tab, or the user's own machine. Nothing
central exists to abuse or to fund, which is why the hosted demo can stay free
permanently rather than until a trial expires.

Everything below follows from that.

## Three tiers, one interface

```
                       ┌──────────────────────────┐
                       │   <nishachar-ide>        │   embeddable component
                       │   (Web Component)        │
                       └────────────┬─────────────┘
                                    │ picks a runtime
                    ┌───────────────┴────────────────┐
                    ▼                                ▼
        ┌───────────────────────┐        ┌──────────────────────┐
        │  Tier 0: browser      │        │  RemoteRuntime       │
        │  Pyodide + Worker     │        │  HTTP -> nishachar   │
        │  no backend, $0       │        └──────────┬───────────┘
        └───────────────────────┘                   │
                                                    ▼
                                       ┌────────────────────────┐
                                       │  Starlette server      │
                                       └──────────┬─────────────┘
                                                  │
                              ┌───────────────────┴──────────────┐
                              ▼                                  ▼
                  ┌──────────────────────┐          ┌──────────────────────┐
                  │  Tier 1: LocalRunner │          │ Tier 2: DockerRunner │
                  │  host toolchains     │          │ sandboxed containers │
                  └──────────────────────┘          └──────────────────────┘
                              └──────────────┬───────────────────┘
                                             ▼
                                   ┌──────────────────┐
                                   │  languages/*.json │  the registry
                                   └──────────────────┘
```

Every backend implements the same interface and returns the same `ExecResult`,
so nothing upstream cares which one ran:

```python
class Runner(Protocol):
    name: str
    def available(self) -> bool: ...
    def run(self, code, language, *, stdin, timeout, output_limit) -> ExecResult: ...
```

`AutoRunner` composes two of them: it uses your installed toolchain when you
have one and falls back to a container when you don't. That is what makes
"runs every language" true on a machine with only Python installed.

## The registry is the product

`languages/*.json` is the single source of truth. It is:

- read by the Python runners to build command lines,
- inlined into the JavaScript bundle at build time (`build.mjs`), so the
  component knows every language without a network call,
- validated in CI against `languages/schema.json`.

No language has code written for it. A language is a name, some extensions, a
command, and a container image.

This is a technical decision and a growth decision at once. The most common
feature request any polyglot tool gets is "please support X", and here the
answer is an 8-line file that a stranger can write correctly on their first
try. Contribution scales with contributors instead of with maintainer hours.

## Why a Web Component

`<nishachar-ide>` is a native custom element, not a React component.

A React component needs a Vue port, a Svelte port, an Angular wrapper, and a
vanilla build — four artefacts, four bug surfaces, four release cadences. A
custom element is one file that works unmodified in React, Vue, Svelte,
Angular, Astro, plain HTML, WordPress, Electron and Tauri.

Shadow DOM comes along with it, which means the host page's CSS cannot break
the editor and the editor's CSS cannot leak out. Theming still works, through
custom properties and `::part()`.

## Tier 0, in detail

The interesting one, because it is what makes the demo free.

- **Python** runs on Pyodide — CPython compiled to WebAssembly, loaded from
  jsDelivr. Roughly 2.7s to boot, then instant.
- **SHE** runs because `she-lang` publishes a pure-Python wheel with no
  required dependencies, so Pyodide's `micropip` installs it *from PyPI, in the
  tab*, in under two seconds. The IDE then invokes SHE's real CLI entry point,
  so browser behaviour matches `she run file.she` exactly.
- **JavaScript** runs in a Worker built from a Blob. A Worker can be
  `terminate()`d, so an infinite loop is a timeout rather than a hung page.

Everything else needs a backend, and the UI says so rather than failing
mysteriously.

## Repository layout

`main` is the front door: README, community files, the website. All source
lives on `v2.0.0`.

```
packages/core/nishachar/
    registry.py      load and resolve languages/*.json
    runners/
        base.py      Runner protocol, ExecResult, output clamping
        local.py     subprocess + timeout + process-tree kill
        docker.py    container flags, derived image cache
    server.py        Starlette API, trust boundaries
    pty_bridge.py    POSIX pty / ConPTY / pipe fallback
    cli.py           the `nishachar` command
    static/          built IDE shell (generated)

packages/web/src/
    index.js         the custom element
    editor.js        CodeMirror wiring, hand-written theme
    modes.js         highlight id -> grammar
    she-mode.js      SHE grammar
    runtime/         browser.js (tier 0), remote.js (tiers 1-2)
    shell/           the standalone IDE page

languages/           the registry
```

## Deliberate omissions

Things a project like this usually has, left out until someone needs them:

- **No auth or multi-user sessions.** It is a single-user local tool.
- **No project/workspace model.** One buffer, one language. Files are the
  filesystem's job.
- **No plugin API.** The registry already covers the extension point that
  matters; a plugin system with no plugins is just indirection.
- **No streaming output.** Runs are bounded by a timeout, and the terminal
  exists for anything genuinely interactive. Streaming would mean a second
  execution path to keep correct.

Each is a real gap, not a claim of completeness. See [ROADMAP.md](ROADMAP.md).
