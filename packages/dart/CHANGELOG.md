# Changelog

## 2.0.0

First release of the Dart client.

- `NishacharClient` for the `nishachar serve` HTTP API: `run()`, `health()` and
  `fetchLanguages()`.
- The full 62-language registry compiled in, so `NishacharClient.languages` and
  `NishacharClient.find()` work offline and with no backend.
- `find()` resolves by id, alias, extension or display name — `python`, `py`,
  `.py` and `Python` all reach the same entry.
- Typed `ExecResult` and `NishacharException`. A program exiting non-zero is a
  result; only transport and server refusals throw.
- Output is always decoded as UTF-8, so non-ASCII program output survives.
- Works in Flutter, Dart CLI and server-side Dart. One dependency: `http`.
