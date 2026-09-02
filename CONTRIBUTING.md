# Contributing

Thanks for being here. This project is designed so that useful contributions
don't require understanding the whole codebase.

## Add a language in 8 lines

The highest-value contribution, and the easiest. No source code involved.

Create `languages/<id>.json`:

```json
{
  "$schema": "./schema.json",
  "id": "ruby",
  "name": "Ruby",
  "extensions": [".rb"],
  "image": "ruby:3.3-slim",
  "run": ["ruby", "{file}"],
  "template": "puts \"Hello from Ruby!\"\n"
}
```

Check it:

```bash
nishachar languages | grep ruby
nishachar run -l ruby -c 'puts "hi"'
```

Open a PR. That's the whole process. Full field reference:
[`languages/README.md`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/develop/languages/README.md).

**Your favourite language is probably missing.** There are thousands; we ship
62.

## Other good first contributions

- **Write a real syntax grammar** for a language currently borrowing another's
  — see the `NEAREST` map in [`packages/web/src/modes.js`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/develop/packages/web/src/modes.js).
- **Fix a wrong command.** Some registry entries are best-effort; if a language
  you know well doesn't run correctly, you are the right person to fix it.
- **Improve an error message.** If something confused you, it will confuse the
  next person.
- **Add an example** to `examples/`.

Issues labelled [`good first issue`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/labels/good%20first%20issue)
are scoped to be finishable in one sitting.

## Setting up

Source lives on the **`develop`** branch. `main` holds the website and
community documents only.

```bash
git clone https://github.com/ni-sh-a-char/ni_sh_a.char-IDE.git
cd ni_sh_a.char-IDE
git checkout develop

pip install -e ".[dev]"          # Python engine + CLI
cd packages/web && npm install   # the web component
npm run build                    # also builds the IDE shell
```

Then:

```bash
nishachar                # the IDE, in your browser
python -m pytest         # the test suite
python -m ruff check .   # lint
```

## Project layout

| Path | What lives there |
|:--|:--|
| `languages/` | the registry — one JSON file per language |
| `packages/core/nishachar/` | Python engine, runners, server, CLI |
| `packages/web/src/` | the `<nishachar-ide>` component |
| `examples/` | runnable sample programs |
| `tests/` | pytest suite |

[ARCHITECTURE.md](ARCHITECTURE.md) explains why it is shaped this way.

## Pull requests

- Branch from `develop`, and target `develop`.
- Keep it focused. One language, one fix, one feature.
- Add a test when you change behaviour. `tests/` shows the style.
- Run `python -m pytest` and `python -m ruff check .` before pushing.
- Describe *why*, not just *what*. The diff already says what.

CI runs tests on Linux, macOS and Windows, validates every registry file, and
builds the web bundle. It has to be green.

## Code style

- **Python** — ruff, 100 columns, type hints on public functions.
- **JavaScript** — ES modules, no framework, no build-time magic beyond esbuild.
- **Comments explain why.** The code already says what it does. A comment
  earns its place by capturing a constraint, a trade-off, or a trap.

## Things to be careful about

This project runs arbitrary code, so some changes need extra thought:

- Anything touching `runners/` — timeouts, output caps and the process-tree
  kill are load-bearing.
- Anything touching `server.py` — the CORS, `Host` and bind-address checks are
  security boundaries, not conveniences. [SECURITY.md](SECURITY.md) explains
  each one.
- Adding a dependency. The Python package has two; the component has one that
  matters. Please justify a third.

## Reporting security issues

Not through issues. See [SECURITY.md](SECURITY.md).

## Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Licence

Contributions are licensed under [Apache 2.0](LICENSE), the project's licence.
You keep copyright in what you write.
