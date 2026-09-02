# The language registry

Every language this IDE runs is one JSON file in this directory. There is no
per-language code anywhere in the project — the runners read these files and
build a command line.

**That means adding a language is a pull request that changes data, not source.**
It is the best first contribution here, and you do not need to understand the
rest of the codebase to make it.

## Add a language in 8 lines

Create `languages/<id>.json`. The filename must match the `id`.

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

That is a complete, working integration.

## Compiled languages

Add `compile`. Steps run in order, and `run` uses the artefact they produce.

```json
{
  "id": "rust",
  "name": "Rust",
  "extensions": [".rs"],
  "image": "rust:1-slim",
  "compile": [["rustc", "{file}", "-o", "{bin}"]],
  "run": ["{bin}"],
  "template": "fn main() {\n    println!(\"Hello!\");\n}\n"
}
```

## Placeholders

| Placeholder | Becomes |
|:--|:--|
| `{file}` | full path to the source file |
| `{bin}` | path the compiled binary should be written to |
| `{dir}` | the working directory |
| `{stem}` | source filename without its extension |

They substitute **inside** an argument, so `"-o{bin}"` works.

Commands are argument vectors, never shell strings. Nothing is passed to a
shell, so there is no quoting to get right and no injection to worry about.

## Every field

| Field | Required | What it does |
|:--|:--:|:--|
| `id` | ✅ | Lowercase identifier; must equal the filename. |
| `name` | ✅ | Display name, e.g. `C++`. |
| `extensions` | ✅ | File extensions with the leading dot. |
| `run` | ✅ | The command that executes the program. |
| `template` | ✅ | Hello-world shown when the language is picked. |
| `aliases` | | Other names users may type, e.g. `["py", "python3"]`. |
| `comment` | | Line-comment prefix, for the editor's comment toggle. |
| `highlight` | | Syntax mode id ([see the map](../packages/web/src/modes.js)). |
| `image` | | Container image for the sandboxed Docker runner. |
| `compile` | | Compile steps, run in order before `run`. |
| `setup` | | Commands to install packages, run at *image build* time only. |
| `filename` | | Exact source filename, when a toolchain demands one (Java needs `Main.java`). |
| `browser` | | `pyodide` or `native`, if the language can run with no backend. |
| `website` | | The language's official homepage. |

### About `setup`

`setup` runs while the container image is being built, when the network is
still available. By the time your code runs, the container has no network at
all. Use it for `pip install`, `npm i -g` and friends.

## Test your addition

```bash
nishachar languages | grep <id>              # it should appear
nishachar run -l <id> -c '<hello world>'     # it should print
python -m pytest tests/test_registry.py      # the schema check
```

CI validates every file in this directory on every pull request, so a typo
fails before a human has to spot it.

## Picking a container image

Prefer an official image with the toolchain already installed
(`python:3.12-slim`, `golang:1-alpine`, `ruby:3.3-slim`). Prefer smaller tags.
If your language has no published image, use a base like `alpine:latest` plus a
`setup` step.

## Choosing a highlight mode

`highlight` maps to a CodeMirror grammar in
[`packages/web/src/modes.js`](../packages/web/src/modes.js). If your language
has no grammar, pick the closest relative — approximate highlighting beats
none. Writing a real grammar for a language currently using a stand-in is a
great second contribution.
