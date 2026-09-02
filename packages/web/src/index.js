/**
 * <nishachar-ide> -- an embeddable polyglot IDE.
 *
 * A native custom element with Shadow DOM, deliberately chosen over a
 * framework component: one artifact works unmodified in React, Vue, Svelte,
 * Angular, Astro, plain HTML, Electron and Tauri, and the shadow root keeps
 * the host page's CSS out of the editor and vice versa.
 *
 *   <nishachar-ide language="she"></nishachar-ide>
 *
 * With no `endpoint`, it runs code in the visitor's own browser and needs no
 * backend at all. Point `endpoint` at a `nishachar serve` instance to unlock
 * every language in the registry.
 */

import { Editor } from './editor.js';
import { BrowserRuntime } from './runtime/browser.js';
import { RemoteRuntime } from './runtime/remote.js';
import { LANGUAGES, VERSION } from './generated/languages.js';

const BY_ID = new Map(LANGUAGES.map((language) => [language.id, language]));
for (const language of LANGUAGES) {
  for (const alias of language.aliases || []) if (!BY_ID.has(alias)) BY_ID.set(alias, language);
  for (const ext of language.extensions || []) if (!BY_ID.has(ext)) BY_ID.set(ext, language);
}

function resolveLanguage(name) {
  const key = String(name || '').trim().toLowerCase();
  return BY_ID.get(key) || BY_ID.get(`.${key}`) || null;
}

const STYLES = `
:host {
  --nsc-bg: #0d0d14;
  --nsc-surface: #14141f;
  --nsc-border: #24243a;
  --nsc-fg: #e6e6f0;
  --nsc-muted: #8a8aa8;
  --nsc-accent: #b48cff;
  --nsc-accent-2: #6ee7b7;
  --nsc-danger: #ff6b81;
  --nsc-radius: 12px;
  --nsc-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", Menlo, Consolas, monospace;
  --nsc-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --nsc-code-size: 13.5px;

  display: block;
  contain: content;
  color-scheme: dark;
  font-family: var(--nsc-sans);
  color: var(--nsc-fg);
  min-height: 260px;
  height: 420px;
}
:host([theme="light"]) {
  --nsc-bg: #ffffff;
  --nsc-surface: #f7f7fb;
  --nsc-border: #e2e2ee;
  --nsc-fg: #1a1a24;
  --nsc-muted: #6b6b85;
  --nsc-accent: #7c3aed;
  --nsc-accent-2: #059669;
  --nsc-danger: #dc2626;
  color-scheme: light;
}
:host([hidden]) { display: none; }

.shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--nsc-bg);
  border: 1px solid var(--nsc-border);
  border-radius: var(--nsc-radius);
  overflow: hidden;
}

.bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--nsc-surface);
  border-bottom: 1px solid var(--nsc-border);
  flex: 0 0 auto;
  flex-wrap: wrap;
}

select {
  appearance: none;
  background: var(--nsc-bg);
  color: var(--nsc-fg);
  border: 1px solid var(--nsc-border);
  border-radius: 8px;
  padding: 6px 28px 6px 10px;
  font: 500 13px var(--nsc-sans);
  cursor: pointer;
  background-image: linear-gradient(45deg, transparent 50%, var(--nsc-muted) 50%),
                    linear-gradient(135deg, var(--nsc-muted) 50%, transparent 50%);
  background-position: calc(100% - 15px) 52%, calc(100% - 10px) 52%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  max-width: 190px;
}
select:focus-visible, button:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--nsc-accent);
  outline-offset: 1px;
}

button.run {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: var(--nsc-accent);
  color: #12081f;
  border: 0;
  border-radius: 8px;
  padding: 7px 15px;
  font: 700 13px var(--nsc-sans);
  cursor: pointer;
  transition: filter .15s ease, opacity .15s ease;
}
:host([theme="light"]) button.run { color: #fff; }
button.run:hover:not(:disabled) { filter: brightness(1.12); }
button.run:disabled { opacity: .55; cursor: progress; }
button.run svg { width: 11px; height: 11px; }

.spacer { flex: 1 1 auto; }

.status {
  font: 500 12px var(--nsc-sans);
  color: var(--nsc-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 46%;
}
.status.err { color: var(--nsc-danger); }
.status.ok { color: var(--nsc-accent-2); }

.badge {
  font: 600 10px/1 var(--nsc-mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--nsc-muted);
  border: 1px solid var(--nsc-border);
  border-radius: 999px;
  padding: 5px 9px;
}

.body { display: flex; flex: 1 1 auto; min-height: 0; }
.body.stacked { flex-direction: column; }

.pane-edit { flex: 1 1 60%; min-width: 0; min-height: 0; overflow: hidden; }
.pane-edit .cm-editor { height: 100%; }

.pane-out {
  flex: 1 1 40%;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--nsc-surface);
  border-left: 1px solid var(--nsc-border);
}
.body.stacked .pane-out { border-left: 0; border-top: 1px solid var(--nsc-border); }

.tabs { display: flex; gap: 2px; padding: 6px 8px 0; flex: 0 0 auto; }
.tab {
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  color: var(--nsc-muted);
  font: 600 11.5px var(--nsc-sans);
  letter-spacing: .03em;
  padding: 5px 9px;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
}
.tab[aria-selected="true"] { color: var(--nsc-fg); border-bottom-color: var(--nsc-accent); }

.out {
  flex: 1 1 auto;
  margin: 0;
  padding: 10px 12px;
  overflow: auto;
  font: var(--nsc-code-size)/1.6 var(--nsc-mono);
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--nsc-fg);
  tab-size: 4;
}
.out .e { color: var(--nsc-danger); }
.out .hint { color: var(--nsc-muted); font-style: italic; }

textarea.stdin {
  flex: 1 1 auto;
  resize: none;
  border: 0;
  outline: 0;
  padding: 10px 12px;
  background: transparent;
  color: var(--nsc-fg);
  font: var(--nsc-code-size)/1.6 var(--nsc-mono);
}
[hidden] { display: none !important; }

.meta {
  flex: 0 0 auto;
  padding: 6px 12px;
  border-top: 1px solid var(--nsc-border);
  font: 500 11px var(--nsc-mono);
  color: var(--nsc-muted);
  display: flex;
  gap: 12px;
}

@media (prefers-reduced-motion: reduce) {
  button.run { transition: none; }
}
`;

const PLAY_ICON = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0.5 L9 5 L1 9.5 Z" fill="currentColor"/></svg>';

/** Strip the common leading indentation from inline HTML code. */
function dedent(text) {
  const lines = text.replace(/\t/g, '  ').split('\n');
  while (lines.length && !lines[0].trim()) lines.shift();
  while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  const indents = lines.filter((l) => l.trim()).map((l) => l.match(/^ */)[0].length);
  const cut = indents.length ? Math.min(...indents) : 0;
  return lines.map((l) => l.slice(cut)).join('\n');
}

export class NishacharIDE extends HTMLElement {
  static observedAttributes = ['language', 'theme', 'endpoint', 'runtime', 'readonly', 'stdin'];
  static version = VERSION;
  static languages = LANGUAGES;

  #editor = null;
  #runtime = null;
  #remote = null;
  #busy = false;
  #ready = false;

  connectedCallback() {
    if (this.#ready) return;
    this.#ready = true;

    const initial = this.getAttribute('code') ?? dedent(this.textContent || '');
    const root = this.attachShadow({ mode: 'open' });
    root.innerHTML = `
      <style>${STYLES}</style>
      <div class="shell">
        <div class="bar" part="toolbar">
          <select class="lang" aria-label="Language"></select>
          <button class="run" part="run-button" type="button">${PLAY_ICON}<span>Run</span></button>
          <span class="status" role="status" aria-live="polite"></span>
          <span class="spacer"></span>
          <span class="badge" title="Where your code runs"></span>
        </div>
        <div class="body">
          <div class="pane-edit" part="editor"></div>
          <div class="pane-out" part="output">
            <div class="tabs" role="tablist">
              <button class="tab" role="tab" data-pane="out" aria-selected="true">Output</button>
              <button class="tab" role="tab" data-pane="in" aria-selected="false" hidden>Input</button>
            </div>
            <pre class="out" role="tabpanel"><span class="hint">Run your code to see output here.</span></pre>
            <textarea class="stdin" role="tabpanel" spellcheck="false"
                      placeholder="Text sent to the program's standard input" hidden></textarea>
            <div class="meta" hidden></div>
          </div>
        </div>
      </div>`;

    this.$ = (selector) => root.querySelector(selector);
    this.#buildLanguageList();
    this.#applyLayout();

    const language = this.currentLanguage;
    this.#editor = new Editor(this.$('.pane-edit'), {
      doc: initial || language.template || '',
      dark: !this.#isLight,
      highlight: language.highlight,
      readOnly: this.hasAttribute('readonly'),
      onChange: (code) => this.#emit('change', { code }),
    });

    this.$('.run').addEventListener('click', () => this.run());
    this.$('.lang').addEventListener('change', (event) => {
      this.setAttribute('language', event.target.value);
    });
    for (const tab of root.querySelectorAll('.tab')) {
      tab.addEventListener('click', () => this.#showPane(tab.dataset.pane));
    }
    this.addEventListener('keydown', (event) => {
      const accel = event.ctrlKey || event.metaKey;
      if (accel && (event.key === 'Enter' || event.key === "'")) {
        event.preventDefault();
        this.run();
      }
    });

    this.#syncStdinTab();
    this.#syncBadge();
    if (!globalThis.ResizeObserver) return;
    this._observer = new ResizeObserver(() => this.#applyLayout());
    this._observer.observe(this);
    this.#emit('ready', { languages: LANGUAGES.length, version: VERSION });
  }

  disconnectedCallback() {
    this._observer?.disconnect();
    this.#editor?.destroy();
    this.#editor = null;
    this.#ready = false;
  }

  attributeChangedCallback(name, previous, value) {
    if (!this.#ready || previous === value) return;
    if (name === 'language') this.#onLanguageChange();
    if (name === 'theme') this.#editor?.setDark(!this.#isLight);
    if (name === 'readonly') this.#editor?.setReadOnly(this.hasAttribute('readonly'));
    if (name === 'stdin') this.#syncStdinTab();
    if (name === 'endpoint' || name === 'runtime') {
      this.#runtime = null;
      this.#remote = null;
      this.#syncBadge();
    }
  }

  // -- public API --------------------------------------------------------

  /** The current source text. */
  get value() {
    return this.#editor ? this.#editor.value : this.getAttribute('code') || '';
  }

  set value(text) {
    if (this.#editor) this.#editor.value = text;
    else this.setAttribute('code', text);
  }

  get language() {
    return this.getAttribute('language') || 'python';
  }

  set language(name) {
    this.setAttribute('language', name);
  }

  get currentLanguage() {
    return resolveLanguage(this.language) || resolveLanguage('python') || LANGUAGES[0];
  }

  /** Text handed to the program on standard input. */
  get stdin() {
    return this.$?.('.stdin')?.value || '';
  }

  set stdin(text) {
    const field = this.$?.('.stdin');
    if (field) field.value = text;
  }

  focus() {
    this.#editor?.focus();
  }

  /** Execute the current buffer. Resolves with the result object. */
  async run() {
    if (this.#busy || !this.#editor) return null;
    const language = this.currentLanguage;
    const code = this.value;

    this.#busy = true;
    this.$('.run').disabled = true;
    this.#setStatus('Running…');
    this.$('.meta').hidden = true;
    this.#emit('run', { language: language.id, code });

    let result;
    try {
      const runtime = await this.#getRuntime(language);
      result = await runtime.run({
        language,
        code,
        stdin: this.stdin,
        timeout: Number(this.getAttribute('timeout')) || undefined,
      });
    } catch (error) {
      result = {
        stdout: '',
        stderr: String(error?.message || error),
        exitCode: 1,
        ok: false,
        durationMs: 0,
        runner: 'none',
        language: language.id,
      };
    } finally {
      this.#busy = false;
      this.$('.run').disabled = false;
    }

    this.#render(result);
    this.#emit('result', result);
    return result;
  }

  // -- internals ---------------------------------------------------------

  get #isLight() {
    const theme = this.getAttribute('theme');
    if (theme === 'light') return true;
    if (theme === 'dark') return false;
    return globalThis.matchMedia?.('(prefers-color-scheme: light)').matches ?? false;
  }

  get #endpoint() {
    return this.getAttribute('endpoint');
  }

  async #getRuntime(language) {
    const mode = (this.getAttribute('runtime') || 'auto').toLowerCase();
    const wantsRemote = mode === 'remote' || (mode === 'auto' && this.#endpoint);

    if (wantsRemote && this.#endpoint) {
      this.#remote ||= new RemoteRuntime(this.#endpoint);
      return this.#remote;
    }
    if (mode === 'remote' && !this.#endpoint) {
      throw new Error('runtime="remote" needs an endpoint attribute.');
    }

    this.#runtime ||= new BrowserRuntime({ onStatus: (text) => this.#setStatus(text) });
    if (!this.#runtime.supports(language)) {
      throw new Error(
        `${language.name} cannot run in the browser. Start a backend with ` +
          '"nishachar serve" and set the endpoint attribute to run it.'
      );
    }
    return this.#runtime;
  }

  #buildLanguageList() {
    const select = this.$('.lang');
    const browserOnly = !this.#endpoint && this.getAttribute('runtime') !== 'remote';
    const runnable = LANGUAGES.filter((l) => l.browser);
    const rest = LANGUAGES.filter((l) => !l.browser);

    const option = (l) => `<option value="${l.id}">${l.name}</option>`;
    if (browserOnly && runnable.length) {
      select.innerHTML =
        `<optgroup label="Runs here, no backend">${runnable.map(option).join('')}</optgroup>` +
        `<optgroup label="Needs a backend">${rest.map(option).join('')}</optgroup>`;
    } else {
      select.innerHTML = LANGUAGES.map(option).join('');
    }
    select.value = this.currentLanguage.id;
  }

  #onLanguageChange() {
    const language = this.currentLanguage;
    this.$('.lang').value = language.id;
    this.#editor.setHighlight(language.highlight);
    // Swap in the new language's starter only if the buffer is untouched or
    // still holds another language's template.
    const current = this.value.trim();
    const isTemplate = !current || LANGUAGES.some((l) => l.template.trim() === current);
    if (isTemplate && language.template) this.#editor.value = language.template;
    this.#setStatus('');
    this.#syncBadge();
  }

  #applyLayout() {
    const stacked =
      this.getAttribute('layout') === 'stacked' ||
      (this.getAttribute('layout') !== 'split' && this.clientWidth < 620);
    this.$('.body').classList.toggle('stacked', stacked);
  }

  #syncStdinTab() {
    const wanted = this.hasAttribute('stdin');
    this.$('.tab[data-pane="in"]').hidden = !wanted;
    if (!wanted) this.#showPane('out');
  }

  #syncBadge() {
    const badge = this.$('.badge');
    if (!badge) return;
    const remote = this.#endpoint && this.getAttribute('runtime') !== 'browser';
    badge.textContent = remote ? 'server' : 'in-browser';
    badge.title = remote
      ? `Executing on ${this.#endpoint}`
      : 'Executing in this tab. No code leaves your browser.';
  }

  #showPane(which) {
    for (const tab of this.shadowRoot.querySelectorAll('.tab')) {
      tab.setAttribute('aria-selected', String(tab.dataset.pane === which));
    }
    this.$('.out').hidden = which !== 'out';
    this.$('.stdin').hidden = which !== 'in';
  }

  #setStatus(text, kind = '') {
    const status = this.$('.status');
    if (!status) return;
    status.textContent = text;
    status.className = `status ${kind}`;
  }

  #render(result) {
    this.#showPane('out');
    const out = this.$('.out');
    const escape = (s) =>
      String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);

    let html = '';
    if (result.stdout) html += escape(result.stdout);
    if (result.stderr) html += `<span class="e">${escape(result.stderr)}</span>`;
    if (!html) html = '<span class="hint">(no output)</span>';
    out.innerHTML = html;
    out.scrollTop = out.scrollHeight;

    const meta = this.$('.meta');
    meta.hidden = false;
    meta.innerHTML =
      `<span>exit ${result.exitCode ?? 0}</span>` +
      `<span>${result.durationMs ?? 0} ms</span>` +
      `<span>${escape(result.runner || '')}</span>` +
      (result.truncated ? '<span>output truncated</span>' : '');

    this.#setStatus(
      result.ok ? 'Done' : result.timedOut ? 'Timed out' : `Exit ${result.exitCode}`,
      result.ok ? 'ok' : 'err'
    );
  }

  #emit(name, detail) {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
  }
}

if (!customElements.get('nishachar-ide')) {
  customElements.define('nishachar-ide', NishacharIDE);
}

export { LANGUAGES, VERSION };
export default NishacharIDE;
