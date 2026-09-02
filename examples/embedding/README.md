# Embedding `<nishachar-ide>`

It is a native custom element. There is no framework wrapper, because there
doesn't need to be one — the same file works everywhere.

## Plain HTML

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/@nishachar/ide"></script>

<nishachar-ide language="she"></nishachar-ide>
```

Give it code inline and the indentation is stripped for you:

```html
<nishachar-ide language="python">
  for i in range(3):
      print("hello", i)
</nishachar-ide>
```

## React

Custom elements work in React 19+ directly. Use `ref` for properties and events.

```jsx
import { useEffect, useRef } from 'react';
import '@nishachar/ide';

export function Playground() {
  const ide = useRef(null);

  useEffect(() => {
    const node = ide.current;
    const onResult = (event) => console.log(event.detail.stdout);
    node.addEventListener('result', onResult);
    return () => node.removeEventListener('result', onResult);
  }, []);

  return <nishachar-ide ref={ide} language="python" theme="dark" />;
}
```

On React 18 and earlier, set non-string props through the ref (`ide.current.value = '...'`)
rather than as JSX attributes.

## Vue

```vue
<script setup>
import '@nishachar/ide';
const onResult = (event) => console.log(event.detail);
</script>

<template>
  <nishachar-ide language="rust" endpoint="http://localhost:8777" @result="onResult" />
</template>
```

Tell Vue it is a custom element so it doesn't warn:

```js
// vite.config.js
export default {
  plugins: [vue({ template: { compilerOptions: {
    isCustomElement: (tag) => tag === 'nishachar-ide',
  } } })],
};
```

## Svelte

```svelte
<script>
  import '@nishachar/ide';
</script>

<nishachar-ide language="go" on:result={(e) => console.log(e.detail)} />
```

## Angular

Add `CUSTOM_ELEMENTS_SCHEMA` to the module or standalone component, then use the
tag as-is.

## Attributes

| Attribute | Values | Meaning |
|:--|:--|:--|
| `language` | any id, alias or extension | Starting language. Default `python`. |
| `code` | source text | Initial buffer. Inline text content works too. |
| `theme` | `dark` · `light` | Follows the OS when unset. |
| `endpoint` | URL | A `nishachar serve` backend. Omit to run in-browser. |
| `runtime` | `auto` · `browser` · `remote` | Where to execute. Default `auto`. |
| `readonly` | present | Editor is not editable. |
| `stdin` | present | Show the standard-input tab. |
| `layout` | `split` · `stacked` | Defaults to width-based. |
| `timeout` | milliseconds | Per-run limit. |

## Properties, methods and events

```js
const ide = document.querySelector('nishachar-ide');

ide.value = 'print("set from JS")';   // read/write the buffer
ide.language = 'python';
ide.stdin = 'piped input';
const result = await ide.run();        // returns the result object

ide.addEventListener('ready',  (e) => console.log(e.detail.languages));
ide.addEventListener('change', (e) => console.log(e.detail.code));
ide.addEventListener('run',    (e) => console.log('running', e.detail.language));
ide.addEventListener('result', (e) => console.log(e.detail.stdout, e.detail.exitCode));
```

## Styling

The shadow root keeps your CSS out and its CSS in. Theme it with custom
properties, and reach the two exposed parts with `::part()`:

```css
nishachar-ide {
  --nsc-accent: #ff4f81;
  --nsc-radius: 4px;
  --nsc-mono: 'JetBrains Mono', monospace;
  height: 600px;
}
nishachar-ide::part(toolbar) { border-bottom-width: 2px; }
```

## Which languages run without a backend?

Python, SHE and JavaScript. Everything else needs `endpoint` pointing at a
running `nishachar serve`. The language dropdown groups them so users can see
which is which.
