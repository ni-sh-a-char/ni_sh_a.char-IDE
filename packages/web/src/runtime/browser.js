/**
 * Tier 0: execute code in the visitor's own browser tab. No backend at all.
 *
 * This is what makes the embedded component work on a static site, and what
 * makes the project's hosted demo cost its maintainer nothing: there is no
 * server to run, meter, or abuse.
 *
 * - Python and SHE run on Pyodide (CPython compiled to WebAssembly). SHE is a
 *   pure-Python wheel with no required dependencies, so micropip installs it
 *   straight from PyPI, in the tab.
 * - JavaScript runs in a Worker, so an infinite loop can be terminated instead
 *   of freezing the page.
 */

const PYODIDE_VERSION = '0.27.2';
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.mjs`;

export class BrowserRuntime {
  constructor({ onStatus } = {}) {
    this.id = 'browser';
    this.onStatus = onStatus || (() => {});
    this._pyodide = null;
    this._loading = null;
    this._sheReady = false;
  }

  get label() {
    return 'browser';
  }

  supports(language) {
    return Boolean(language && language.browser);
  }

  async run({ language, code, stdin = '', timeout = 15000 }) {
    const started = performance.now();
    const finish = (result) => ({
      stdout: '',
      stderr: '',
      exitCode: 0,
      timedOut: false,
      truncated: false,
      runner: 'browser',
      language: language.id,
      ...result,
      durationMs: Math.round(performance.now() - started),
      ok: (result.exitCode ?? 0) === 0 && !result.timedOut,
    });

    if (language.browser === 'pyodide') {
      return finish(await this._runPython(language, code, stdin));
    }
    if (language.browser === 'native') {
      return finish(await this._runJavaScript(code, timeout));
    }
    return finish({
      stderr:
        `${language.name} cannot run in the browser. Connect a backend ` +
        `(nishachar serve) to run it, or pick a language marked "browser".`,
      exitCode: 1,
    });
  }

  // -- Python / SHE ------------------------------------------------------

  async _loadPyodide() {
    if (this._pyodide) return this._pyodide;
    if (this._loading) return this._loading;

    this._loading = (async () => {
      this.onStatus('Downloading Python runtime…');
      const { loadPyodide } = await import(/* @vite-ignore */ PYODIDE_URL);
      const pyodide = await loadPyodide({
        indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
      });
      this._pyodide = pyodide;
      this.onStatus('');
      return pyodide;
    })();

    try {
      return await this._loading;
    } catch (error) {
      this._loading = null;
      throw error;
    }
  }

  async _ensureShe(pyodide) {
    if (this._sheReady) return;
    this.onStatus('Installing she-lang from PyPI…');
    await pyodide.loadPackage('micropip');
    const micropip = pyodide.pyimport('micropip');
    await micropip.install('she-lang');
    this._sheReady = true;
    this.onStatus('');
  }

  async _runPython(language, code, stdin) {
    let pyodide;
    try {
      pyodide = await this._loadPyodide();
      if (language.id === 'she') await this._ensureShe(pyodide);
    } catch (error) {
      return {
        stderr: `Could not start the in-browser runtime: ${error.message || error}`,
        exitCode: 1,
      };
    }

    const out = [];
    const err = [];
    pyodide.setStdout({ batched: (line) => out.push(line) });
    pyodide.setStderr({ batched: (line) => err.push(line) });
    if (stdin) {
      const lines = stdin.split('\n');
      let cursor = 0;
      pyodide.setStdin({ stdin: () => (cursor < lines.length ? lines[cursor++] : null) });
    }

    let exitCode = 0;
    try {
      if (language.id === 'she') {
        pyodide.FS.writeFile('/tmp/main.she', code);
        await pyodide.runPythonAsync(SHE_DRIVER);
      } else {
        await pyodide.runPythonAsync(code);
      }
    } catch (error) {
      const text = String(error.message || error);
      // Pyodide wraps a Python traceback in a JS Error; the traceback is the
      // useful part, so show that rather than the wrapper.
      err.push(text.replace(/^PythonError:\s*/, ''));
      exitCode = 1;
    } finally {
      pyodide.setStdout({});
      pyodide.setStderr({});
      pyodide.setStdin({});
    }

    return {
      stdout: out.join('\n') + (out.length ? '\n' : ''),
      stderr: err.join('\n') + (err.length ? '\n' : ''),
      exitCode,
    };
  }

  // -- JavaScript --------------------------------------------------------

  _runJavaScript(code, timeout) {
    return new Promise((resolve) => {
      let worker;
      try {
        const blob = new Blob([JS_WORKER], { type: 'text/javascript' });
        worker = new Worker(URL.createObjectURL(blob));
      } catch (error) {
        return resolve({ stderr: `Could not start a Worker: ${error}`, exitCode: 1 });
      }

      const timer = setTimeout(() => {
        worker.terminate();
        resolve({
          stderr: `Killed: exceeded the ${(timeout / 1000).toFixed(0)}s time limit.`,
          exitCode: 124,
          timedOut: true,
        });
      }, timeout);

      worker.onmessage = (event) => {
        clearTimeout(timer);
        worker.terminate();
        resolve(event.data);
      };
      worker.onerror = (event) => {
        clearTimeout(timer);
        worker.terminate();
        resolve({ stderr: event.message || 'worker error', exitCode: 1 });
      };
      worker.postMessage(code);
    });
  }
}

/** Runs SHE's own CLI inside Pyodide, exactly as `she run file.she` would. */
const SHE_DRIVER = `
import sys
_argv = sys.argv
sys.argv = ["she", "run", "/tmp/main.she"]
try:
    from she.cli import main
    main()
except SystemExit as exit_:
    if exit_.code:
        raise
finally:
    sys.argv = _argv
`;

/** The JS sandbox. Console output is collected and returned in one message. */
const JS_WORKER = `
self.onmessage = async (event) => {
  const out = [], err = [];
  const show = (value) => {
    if (typeof value === 'string') return value;
    try { return JSON.stringify(value, null, 2) ?? String(value); }
    catch { return String(value); }
  };
  const write = (sink) => (...args) => sink.push(args.map(show).join(' '));
  console.log = console.info = console.debug = write(out);
  console.warn = console.error = write(err);

  let exitCode = 0;
  try {
    const body = event.data;
    const run = new Function('return (async () => {' + body + '\\n})()');
    await run();
  } catch (error) {
    err.push(String((error && error.stack) || error));
    exitCode = 1;
  }
  self.postMessage({
    stdout: out.join('\\n') + (out.length ? '\\n' : ''),
    stderr: err.join('\\n') + (err.length ? '\\n' : ''),
    exitCode,
  });
};
`;
