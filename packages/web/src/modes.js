/**
 * Maps a registry `highlight` id to a CodeMirror extension.
 *
 * Most languages come from `@codemirror/legacy-modes`, which is one dependency
 * covering ~90 grammars. Languages without a grammar of their own fall back to
 * the closest relative -- Zig reads fine as C, Racket as Scheme -- which is a
 * far better experience than no highlighting at all.
 */

import { StreamLanguage } from '@codemirror/language';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';

import { sheMode } from './she-mode.js';

import * as clike from '@codemirror/legacy-modes/mode/clike';
import * as mllike from '@codemirror/legacy-modes/mode/mllike';
import { shell } from '@codemirror/legacy-modes/mode/shell';
import { powerShell } from '@codemirror/legacy-modes/mode/powershell';
import { ruby } from '@codemirror/legacy-modes/mode/ruby';
import { perl } from '@codemirror/legacy-modes/mode/perl';
import { lua } from '@codemirror/legacy-modes/mode/lua';
import { r } from '@codemirror/legacy-modes/mode/r';
import { julia } from '@codemirror/legacy-modes/mode/julia';
import { go } from '@codemirror/legacy-modes/mode/go';
import { rust } from '@codemirror/legacy-modes/mode/rust';
import { haskell } from '@codemirror/legacy-modes/mode/haskell';
import { erlang } from '@codemirror/legacy-modes/mode/erlang';
import { clojure } from '@codemirror/legacy-modes/mode/clojure';
import { commonLisp } from '@codemirror/legacy-modes/mode/commonlisp';
import { scheme } from '@codemirror/legacy-modes/mode/scheme';
import { swift } from '@codemirror/legacy-modes/mode/swift';
import { pascal } from '@codemirror/legacy-modes/mode/pascal';
import { fortran } from '@codemirror/legacy-modes/mode/fortran';
import { cobol } from '@codemirror/legacy-modes/mode/cobol';
import { tcl } from '@codemirror/legacy-modes/mode/tcl';
import { d } from '@codemirror/legacy-modes/mode/d';
import { elm } from '@codemirror/legacy-modes/mode/elm';
import { coffeeScript } from '@codemirror/legacy-modes/mode/coffeescript';
import { groovy } from '@codemirror/legacy-modes/mode/groovy';
import { crystal } from '@codemirror/legacy-modes/mode/crystal';
import { haxe } from '@codemirror/legacy-modes/mode/haxe';
import { brainfuck } from '@codemirror/legacy-modes/mode/brainfuck';
import { gas } from '@codemirror/legacy-modes/mode/gas';
import { standardSQL } from '@codemirror/legacy-modes/mode/sql';

const stream = (mode) => StreamLanguage.define(mode);

/** highlight id -> extension factory. Kept lazy so unused modes cost nothing. */
const MODES = {
  she: () => stream(sheMode),
  python: () => python(),
  javascript: () => javascript(),
  typescript: () => javascript({ typescript: true }),

  c: () => stream(clike.c),
  cpp: () => stream(clike.cpp),
  java: () => stream(clike.java),
  csharp: () => stream(clike.csharp),
  scala: () => stream(clike.scala),
  kotlin: () => stream(clike.kotlin),
  objectivec: () => stream(clike.objectiveC),
  dart: () => stream(clike.dart),

  ocaml: () => stream(mllike.oCaml),
  fsharp: () => stream(mllike.fSharp),

  shell: () => stream(shell),
  powershell: () => stream(powerShell),
  ruby: () => stream(ruby),
  perl: () => stream(perl),
  lua: () => stream(lua),
  r: () => stream(r),
  julia: () => stream(julia),
  go: () => stream(go),
  rust: () => stream(rust),
  haskell: () => stream(haskell),
  erlang: () => stream(erlang),
  clojure: () => stream(clojure),
  commonlisp: () => stream(commonLisp),
  scheme: () => stream(scheme),
  swift: () => stream(swift),
  pascal: () => stream(pascal),
  fortran: () => stream(fortran),
  cobol: () => stream(cobol),
  tcl: () => stream(tcl),
  d: () => stream(d),
  elm: () => stream(elm),
  coffeescript: () => stream(coffeeScript),
  groovy: () => stream(groovy),
  crystal: () => stream(crystal),
  haxe: () => stream(haxe),
  brainfuck: () => stream(brainfuck),
  assembly: () => stream(gas),
  sql: () => stream(standardSQL),
};

/**
 * Languages with no grammar of their own, mapped to their nearest relative.
 * Approximate highlighting beats none, and each of these is a genuinely good
 * first contribution if someone wants to write the real grammar.
 */
const NEAREST = {
  php: 'cpp',
  elixir: 'ruby',
  nim: 'python',
  zig: 'cpp',
  prolog: 'erlang',
  racket: 'scheme',
  ada: 'pascal',
  awk: 'c',
  vlang: 'go',
  gleam: 'rust',
  wren: 'javascript',
  io: 'javascript',
  vala: 'csharp',
  solidity: 'javascript',
};

export function modeFor(highlight) {
  const key = String(highlight || '').toLowerCase();
  const factory = MODES[key] || MODES[NEAREST[key]];
  return factory ? factory() : [];
}

export const HIGHLIGHT_IDS = Object.keys(MODES);
