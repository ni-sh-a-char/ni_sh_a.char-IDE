# nishachar_ide

**Run any language, anywhere.** A Dart and Flutter client for the
[ni_sh_a.char-IDE](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE) polyglot
execution engine — with the full **62-language registry compiled in**, so it
works before you have a server and keeps working offline.

[![pub package](https://img.shields.io/pub/v/nishachar_ide.svg)](https://pub.dev/packages/nishachar_ide)
[![License](https://img.shields.io/badge/license-Apache--2.0-D22128.svg)](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/main/LICENSE)

## Install

```yaml
dependencies:
  nishachar_ide: ^2.0.0
```

## Use the registry with no server

The language list ships inside the package. No network, no backend, no setup.

```dart
import 'package:nishachar_ide/nishachar_ide.dart';

NishacharClient.languages.length;          // 62
NishacharClient.find('.rs')?.name;         // Rust
NishacharClient.find('py')?.template;      // print("Hello from Python!")

final she = NishacharClient.find('she')!;
she.runsInBrowser;                          // true
she.extensions;                             // ['.she']
```

`find()` resolves by id, alias, extension or display name — `python`, `py`,
`.py` and `Python` all reach the same entry.

## Run code

Start a backend:

```bash
pip install nishachar-ide
nishachar serve
```

Then:

```dart
final client = NishacharClient(Uri.parse('http://localhost:8777'));

final result = await client.run(
  language: 'she',
  code: 'say "Hello from Dart!"',
  timeout: const Duration(seconds: 10),
);

print(result.stdout);      // Hello from Dart!
print(result.exitCode);    // 0
print(result.durationMs);  // 158
print(result.runner);      // local

client.close();
```

### Standard input

```dart
await client.run(
  language: 'python',
  code: 'print(input().upper())',
  stdin: 'quiet\n',
); // -> QUIET
```

### Errors

A program that exits non-zero is a **result**, not an exception — that is
normal program behaviour, and you almost always want to show it to the user:

```dart
final result = await client.run(language: 'py', code: 'raise SystemExit(3)');
result.ok;        // false
result.exitCode;  // 3
result.stderr;    // the traceback
```

`NishacharException` is thrown only when the request itself fails — an unknown
language, a malformed request, or an unreachable backend:

```dart
try {
  await client.run(language: 'klingon', code: 'x');
} on NishacharException catch (error) {
  print('${error.statusCode}: ${error.message}'); // 404: unknown language 'klingon'
}
```

## In Flutter

The client is pure Dart with a single dependency (`http`), so it works
unchanged in Flutter on every platform. Point it at a backend you run, and
build whatever UI you like on top:

```dart
final _client = NishacharClient(Uri.parse('https://your-backend.example'));

Future<void> _run() async {
  final result = await _client.run(language: _language, code: _controller.text);
  setState(() => _output = result.stdout + result.stderr);
}

@override
void dispose() {
  _client.close();
  super.dispose();
}
```

Remember to `close()` the client when you are done with it.

## Which languages can run?

All 62 are in the registry, but what a given backend can execute depends on the
toolchains it has. Ask it:

```dart
final available = await client.fetchLanguages();
final health = await client.health(); // version, runner, language count
```

## Security

This library talks to a server that executes arbitrary code. Point it only at a
backend you control, and read
[SECURITY.md](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/main/SECURITY.md)
before exposing one to anybody else — in particular, the server's default local
runner has **no isolation**, and `--runner docker` exists for untrusted input.

## Links

- [Live demo](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/) — runs SHE and Python in your browser, no backend
- [Documentation](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/docs/)
- [Repository](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE)
- [Add a language](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/v2.0.0/languages/README.md) — 8 lines of JSON

Apache-2.0 © Piyush Mishra
