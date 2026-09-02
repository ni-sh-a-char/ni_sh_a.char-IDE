# @nishachar/ide

**Run any language, anywhere.** An embeddable polyglot IDE as a native web
component — one file that works in React, Vue, Svelte, Angular, Astro, plain
HTML, Electron and Tauri.

[![npm](https://img.shields.io/npm/v/@nishachar/ide?logo=npm&color=CB3837)](https://www.npmjs.com/package/@nishachar/ide)
[![License](https://img.shields.io/badge/license-Apache--2.0-D22128.svg)](./LICENSE)

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/@nishachar/ide"></script>

<nishachar-ide language="python"></nishachar-ide>
```

That's it. **No backend.** Python, [SHE](https://github.com/ni-sh-a-char/SHE)
and JavaScript execute in the visitor's own browser via WebAssembly, so an
embed on a static site costs you nothing to run and sends no code anywhere.

## Install

```bash
npm install @nishachar/ide
```

```js
import '@nishachar/ide';
```

## All 62 languages

Point it at a [`nishachar serve`](https://pypi.org/project/nishachar-ide/)
backend and the other 59 languages become available too:

```html
<nishachar-ide language="rust" endpoint="http://localhost:8777"></nishachar-ide>
```

```bash
pip install nishachar-ide
nishachar serve --cors https://your-site.example
```

## Attributes

| Attribute | Values | Meaning |
|:--|:--|:--|
| `language` | id, alias or extension | Starting language. Default `python`. |
| `code` | source text | Initial buffer. Inline text content works too. |
| `theme` | `dark` · `light` | Follows the OS when unset. |
| `endpoint` | URL | Backend to execute against. Omit to run in-browser. |
| `runtime` | `auto` · `browser` · `remote` | Default `auto`. |
| `readonly` | present | Editor is not editable. |
| `stdin` | present | Show the standard-input tab. |
| `layout` | `split` · `stacked` | Defaults to width-based. |
| `timeout` | milliseconds | Per-run limit. |

## API

```js
const ide = document.querySelector('nishachar-ide');

ide.value = 'print("hello")';
ide.language = 'python';
const result = await ide.run();     // { stdout, stderr, exitCode, durationMs, ok }

ide.addEventListener('result', (e) => console.log(e.detail.stdout));
ide.addEventListener('change', (e) => console.log(e.detail.code));
ide.addEventListener('ready',  (e) => console.log(e.detail.languages));
```

## Theming

Shadow DOM keeps your styles out and its styles in. Theme through custom
properties:

```css
nishachar-ide {
  --nsc-accent: #ff4f81;
  --nsc-bg: #000;
  --nsc-mono: 'JetBrains Mono', monospace;
  --nsc-radius: 4px;
  height: 600px;
}
nishachar-ide::part(toolbar) { border-bottom: 2px solid var(--nsc-accent); }
```

## Framework notes

Full examples for React, Vue, Svelte and Angular:
[examples/embedding](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/v2.0.0/examples/embedding/README.md).

## Links

- [Live demo](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/)
- [Repository](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE)
- [Add a language](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/v2.0.0/languages/README.md)

Apache-2.0 © Piyush Mishra
