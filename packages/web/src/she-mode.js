/**
 * A CodeMirror stream mode for SHE.
 *
 * SHE reads like English, so highlighting leans on keywords rather than
 * punctuation, and on the `{name}` interpolation inside strings.
 * https://github.com/ni-sh-a-char/SHE
 */

const KEYWORDS = new Set([
  'let', 'be', 'set', 'to', 'say', 'ask', 'fun', 'function', 'return', 'give',
  'if', 'else', 'then', 'unless', 'while', 'until', 'for', 'each', 'in', 'do',
  'end', 'and', 'or', 'not', 'is', 'isnt', 'import', 'use', 'from', 'as',
  'try', 'catch', 'finally', 'throw', 'break', 'continue', 'repeat', 'times',
  'when', 'match', 'with', 'where', 'of', 'call',
]);

/** SHE's headline feature: capabilities the program must ask for. */
const PERMISSIONS = new Set([
  'allow', 'deny', 'permit', 'network', 'filesystem', 'file', 'shell',
  'process', 'env', 'read', 'write', 'execute', 'require',
]);

const ATOMS = new Set(['true', 'false', 'yes', 'no', 'nothing', 'null', 'none', 'empty']);

export const sheMode = {
  name: 'she',

  startState() {
    return { inString: null };
  },

  token(stream, state) {
    // Continue a string that spans the token boundary (interpolation splits it).
    if (state.inString) {
      return readString(stream, state);
    }

    if (stream.eatSpace()) return null;

    // Comments: # to end of line.
    if (stream.peek() === '#') {
      stream.skipToEnd();
      return 'comment';
    }

    const quote = stream.peek();
    if (quote === '"' || quote === "'") {
      stream.next();
      state.inString = quote;
      return readString(stream, state);
    }

    if (/\d/.test(stream.peek())) {
      stream.eatWhile(/[\d._]/);
      return 'number';
    }

    // `->` is SHE's expression-body arrow.
    if (stream.match('->') || stream.match('=>')) return 'operator';
    if (stream.match(/^[=+\-*/%<>!]+/)) return 'operator';
    if (stream.match(/^[(){}[\],:;]/)) return 'punctuation';

    if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/)) {
      const word = stream.current().toLowerCase();
      if (PERMISSIONS.has(word)) return 'keyword';
      if (KEYWORDS.has(word)) return 'keyword';
      if (ATOMS.has(word)) return 'atom';
      // A name directly followed by `(` is being called.
      if (stream.peek() === '(') return 'variableName.function';
      return 'variableName';
    }

    stream.next();
    return null;
  },

  languageData: {
    commentTokens: { line: '#' },
    indentOnInput: /^\s*end$/,
  },
};

function readString(stream, state) {
  const quote = state.inString;
  let escaped = false;
  while (!stream.eol()) {
    const ch = stream.next();
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === '\\') {
      escaped = true;
      continue;
    }
    // Highlight `{expr}` interpolation distinctly from the surrounding text.
    if (ch === '{') {
      stream.backUp(1);
      if (stream.current().length) return 'string';
      stream.next();
      stream.eatWhile((c) => c !== '}');
      stream.eat('}');
      return 'string.special';
    }
    if (ch === quote) {
      state.inString = null;
      return 'string';
    }
  }
  // Unterminated at end of line -- SHE strings are single-line.
  state.inString = null;
  return 'string';
}
