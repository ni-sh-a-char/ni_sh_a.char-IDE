/**
 * The standalone IDE, served by `nishachar`.
 *
 * It is the same <nishachar-ide> component everyone else embeds, pointed at
 * the local server and given a real terminal alongside it. Nothing here is
 * private to the desktop build.
 */

import '../index.js';
import '@xterm/xterm/css/xterm.css';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';

const ide = document.getElementById('ide');
const origin = location.origin;
ide.setAttribute('endpoint', origin);

const $ = (id) => document.getElementById(id);

let health = null;

async function boot() {
  try {
    health = await (await fetch(`${origin}/api/health`)).json();
  } catch {
    $('runner-chip').textContent = 'offline';
    return;
  }
  $('version').textContent = `v${health.version}`;
  $('lang-count').textContent = health.languages;
  $('runner-chip').textContent = `runner: ${health.runner}`;
  document.title = `ni_sh_a.char-IDE ${health.version}`;
}

// -- terminal -------------------------------------------------------------

let terminal = null;
let socket = null;
let fit = null;

function openTerminal() {
  if (terminal) return;

  if (!health?.shell) {
    $('term').hidden = true;
    const note = $('term-note');
    note.hidden = false;
    note.innerHTML =
      'The terminal is disabled. It is off by default because it exposes an ' +
      'interactive shell.<br><br>Restart with <code>nishachar --allow-shell</code> to enable it.';
    return;
  }

  terminal = new Terminal({
    fontFamily: 'ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace',
    fontSize: 13,
    cursorBlink: true,
    theme: {
      background: '#07070d',
      foreground: '#e6e6f0',
      cursor: '#b48cff',
      selectionBackground: '#2a2440',
      black: '#14141f', red: '#ff6b81', green: '#6ee7b7', yellow: '#ffb86c',
      blue: '#7dd3fc', magenta: '#b48cff', cyan: '#67e8f9', white: '#e6e6f0',
    },
  });
  fit = new FitAddon();
  terminal.loadAddon(fit);
  terminal.open($('term'));
  fit.fit();

  const url = `${origin.replace(/^http/, 'ws')}/api/pty`;
  socket = new WebSocket(url);
  $('term-status').textContent = 'connecting…';

  socket.onopen = () => {
    $('term-status').textContent = 'connected';
    sendResize();
  };
  socket.onmessage = (event) => terminal.write(event.data);
  socket.onclose = () => {
    $('term-status').textContent = 'disconnected';
    terminal?.write('\r\n\x1b[2m[session ended]\x1b[0m\r\n');
  };
  socket.onerror = () => {
    $('term-status').textContent = 'error';
  };

  terminal.onData((data) => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'input', data }));
    }
  });
}

function sendResize() {
  if (!terminal || socket?.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({ type: 'resize', cols: terminal.cols, rows: terminal.rows }));
}

$('toggle-term').addEventListener('click', (event) => {
  const wrap = $('term-wrap');
  const showing = wrap.hidden;
  wrap.hidden = !showing;
  event.currentTarget.setAttribute('aria-pressed', String(showing));
  if (showing) {
    openTerminal();
    requestAnimationFrame(() => {
      fit?.fit();
      sendResize();
      terminal?.focus();
    });
  }
});

let resizeTimer;
addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (!$('term-wrap').hidden) {
      fit?.fit();
      sendResize();
    }
  }, 120);
});

// Ctrl/Cmd+` toggles the terminal, matching every other editor.
addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === '`') {
    event.preventDefault();
    $('toggle-term').click();
  }
});

boot();
