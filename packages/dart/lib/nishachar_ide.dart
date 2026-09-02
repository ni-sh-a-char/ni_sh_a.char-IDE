/// Run any language, anywhere.
///
/// A Dart and Flutter client for the [ni_sh_a.char-IDE](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE)
/// polyglot execution engine, with the full 62-language registry compiled in.
///
/// ```dart
/// import 'package:nishachar_ide/nishachar_ide.dart';
///
/// void main() async {
///   final client = NishacharClient(Uri.parse('http://localhost:8777'));
///   final result = await client.run(language: 'she', code: 'say "hello"');
///   print(result.stdout); // hello
///   client.close();
/// }
/// ```
///
/// The registry works with no server at all:
///
/// ```dart
/// NishacharClient.languages.length;   // 62
/// NishacharClient.find('.rs')?.name;  // Rust
/// ```
library;

export 'src/client.dart' show ExecResult, NishacharClient, NishacharException;
export 'src/language.dart' show Language;
export 'src/registry.g.dart' show kLanguages;
