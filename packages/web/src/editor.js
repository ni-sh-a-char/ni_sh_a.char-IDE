/**
 * CodeMirror wiring: one editor whose language, theme and read-only state can
 * be swapped without rebuilding it.
 *
 * The syntax theme is hand-written rather than pulled from a package. It is
 * one less dependency, and it lets the component look like itself instead of
 * like every other CodeMirror embed.
 */

import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection, rectangularSelection, crosshairCursor, highlightSpecialChars } from '@codemirror/view';
import { EditorState, Compartment } from '@codemirror/state';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search';
import { closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap } from '@codemirror/autocomplete';
import {
  HighlightStyle,
  syntaxHighlighting,
  indentOnInput,
  bracketMatching,
  foldGutter,
  foldKeymap,
} from '@codemirror/language';
import { tags as t } from '@lezer/highlight';

import { modeFor } from './modes.js';

const PALETTE = {
  dark: {
    bg: '#0d0d14',
    gutter: '#5a5a72',
    fg: '#e6e6f0',
    caret: '#b48cff',
    selection: '#2a2440',
    active: '#15151f',
    comment: '#5a5a72',
    keyword: '#b48cff',
    string: '#6ee7b7',
    number: '#ffb86c',
    fn: '#7dd3fc',
    type: '#f0abfc',
    operator: '#94a3b8',
    invalid: '#ff6b81',
  },
  light: {
    bg: '#ffffff',
    gutter: '#a0a0b8',
    fg: '#1a1a24',
    caret: '#7c3aed',
    selection: '#e9e2ff',
    active: '#f7f5ff',
    comment: '#8a8aa0',
    keyword: '#7c3aed',
    string: '#059669',
    number: '#c2410c',
    fn: '#0284c7',
    type: '#a21caf',
    operator: '#64748b',
    invalid: '#dc2626',
  },
};

function baseTheme(colors, dark) {
  return EditorView.theme(
    {
      '&': { color: colors.fg, backgroundColor: colors.bg, height: '100%' },
      '.cm-content': {
        caretColor: colors.caret,
        fontFamily: 'var(--nsc-mono)',
        fontSize: 'var(--nsc-code-size)',
        padding: '12px 0',
      },
      '.cm-cursor, .cm-dropCursor': { borderLeftColor: colors.caret, borderLeftWidth: '2px' },
      '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
        backgroundColor: colors.selection,
      },
      '.cm-activeLine': { backgroundColor: colors.active },
      '.cm-gutters': {
        backgroundColor: colors.bg,
        color: colors.gutter,
        border: 'none',
        fontFamily: 'var(--nsc-mono)',
      },
      '.cm-activeLineGutter': { backgroundColor: colors.active, color: colors.fg },
      '.cm-foldPlaceholder': {
        backgroundColor: colors.selection,
        border: 'none',
        color: colors.fg,
      },
      '.cm-scroller': { fontFamily: 'var(--nsc-mono)', lineHeight: '1.6' },
      '.cm-tooltip': {
        backgroundColor: colors.active,
        border: `1px solid ${colors.selection}`,
        borderRadius: '8px',
      },
      '.cm-selectionMatch': { backgroundColor: colors.selection },
    },
    { dark }
  );
}

function highlightStyle(colors) {
  return HighlightStyle.define([
    { tag: [t.comment, t.lineComment, t.blockComment], color: colors.comment, fontStyle: 'italic' },
    { tag: [t.keyword, t.modifier, t.controlKeyword, t.moduleKeyword], color: colors.keyword },
    { tag: [t.string, t.special(t.string), t.regexp], color: colors.string },
    { tag: [t.number, t.bool, t.atom, t.null], color: colors.number },
    { tag: [t.function(t.variableName), t.function(t.propertyName), t.labelName], color: colors.fn },
    { tag: [t.typeName, t.className, t.namespace, t.tagName], color: colors.type },
    { tag: [t.operator, t.punctuation, t.separator, t.bracket], color: colors.operator },
    { tag: [t.propertyName, t.attributeName], color: colors.fn },
    { tag: [t.variableName, t.definition(t.variableName)], color: colors.fg },
    { tag: [t.meta, t.processingInstruction], color: colors.comment },
    { tag: t.invalid, color: colors.invalid },
    { tag: [t.heading, t.strong], fontWeight: '700' },
    { tag: [t.emphasis], fontStyle: 'italic' },
    { tag: [t.link], textDecoration: 'underline' },
    { tag: t.strikethrough, textDecoration: 'line-through' },
  ]);
}

export class Editor {
  constructor(parent, { doc = '', dark = true, highlight = 'text', readOnly = false, onChange } = {}) {
    this.language = new Compartment();
    this.theming = new Compartment();
    this.editable = new Compartment();

    this.view = new EditorView({
      parent,
      state: EditorState.create({
        doc,
        extensions: [
          lineNumbers(),
          highlightActiveLineGutter(),
          highlightSpecialChars(),
          history(),
          foldGutter(),
          drawSelection(),
          EditorState.allowMultipleSelections.of(true),
          indentOnInput(),
          bracketMatching(),
          closeBrackets(),
          autocompletion(),
          rectangularSelection(),
          crosshairCursor(),
          highlightActiveLine(),
          highlightSelectionMatches(),
          keymap.of([
            ...closeBracketsKeymap,
            ...defaultKeymap,
            ...searchKeymap,
            ...historyKeymap,
            ...foldKeymap,
            ...completionKeymap,
            indentWithTab,
          ]),
          this.language.of(modeFor(highlight)),
          this.theming.of(this.themeExtensions(dark)),
          this.editable.of(EditorView.editable.of(!readOnly)),
          EditorView.updateListener.of((update) => {
            if (update.docChanged && onChange) onChange(this.value);
          }),
        ],
      }),
    });
  }

  themeExtensions(dark) {
    const colors = PALETTE[dark ? 'dark' : 'light'];
    return [baseTheme(colors, dark), syntaxHighlighting(highlightStyle(colors))];
  }

  get value() {
    return this.view.state.doc.toString();
  }

  set value(text) {
    this.view.dispatch({
      changes: { from: 0, to: this.view.state.doc.length, insert: text ?? '' },
    });
  }

  setHighlight(highlight) {
    this.view.dispatch({ effects: this.language.reconfigure(modeFor(highlight)) });
  }

  setDark(dark) {
    this.view.dispatch({ effects: this.theming.reconfigure(this.themeExtensions(dark)) });
  }

  setReadOnly(readOnly) {
    this.view.dispatch({
      effects: this.editable.reconfigure(EditorView.editable.of(!readOnly)),
    });
  }

  focus() {
    this.view.focus();
  }

  destroy() {
    this.view.destroy();
  }
}
