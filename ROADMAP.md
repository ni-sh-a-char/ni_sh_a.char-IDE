# Roadmap

What's next, and what was deliberately left out of 2.0.0. Everything here is
open to contribution — several items are tagged
[`good first issue`](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/labels/good%20first%20issue).

## Now (2.1)

- **More languages.** 62 is a start, not a finish. Each is
  [8 lines of JSON](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/v2.0.0/languages/README.md).
- **Real grammars** for languages currently borrowing a relative's
  highlighting — Elixir, Nim, Zig, Prolog, Solidity and PHP all deserve better
  than a stand-in. See `NEAREST` in `packages/web/src/modes.js`.
- **Streaming output.** Runs are currently buffered until the process exits,
  which is fine inside a 10s timeout but poor for a program that prints
  progressively. Needs a second execution path kept consistent with the first.
- **Registry accuracy pass.** Some entries are best-effort and have not been
  exercised against a real toolchain. If you know a language well, verifying
  its entry is a genuinely useful contribution.

## Next (2.2)

- **More languages in the browser.** Ruby (ruby.wasm), PHP (php-wasm), SQLite,
  Lua and anything with a WASI build could join Tier 0. Each removes a reason
  to need a backend.
- **TypeScript in the browser**, which needs a transpiler; `esbuild-wasm`
  loaded on demand is the likely route. Deliberately not shipped in 2.0.0
  rather than claimed and broken.
- **Multi-file projects.** One buffer covers snippets and demos; it does not
  cover anything with an import.
- **Shareable links** that encode the language and source in the URL fragment,
  so nothing is stored server-side and the cost stays zero.
- **VS Code extension** reusing the same registry.

## Later

- **Firecracker or gVisor tier** for people running genuinely hostile input,
  where a shared kernel is not good enough.
- **Package installation per run**, sandboxed — the most requested feature of
  every playground, and the hardest to do safely.
- **Collaborative editing**, if there is demand and a way to do it without a
  server anyone has to pay for.
- **A REPL mode** for languages with one, over the existing PTY channel.

## Explicitly not planned

Saying no is part of a roadmap.

- **A hosted "run anything" API.** It is the one thing this architecture exists
  to avoid. Open code execution as a free service gets abused within hours, and
  a project that depends on someone's credit card is a project with an expiry
  date.
- **Accounts, teams, billing.** Not a SaaS.
- **A plugin system.** The registry is the extension point that matters. A
  plugin API with no plugins is indirection with a changelog.
- **An Electron build.** The browser you already have is a fine window. A
  300 MB download to avoid a `localhost` URL is a bad trade.

## Have an opinion?

Open a [discussion](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/discussions).
Priorities here follow what people actually ask for.
