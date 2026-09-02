// ignore_for_file: avoid_print
//
// Run this against a local backend:
//
//   pip install nishachar-ide && nishachar serve
//   dart run example/nishachar_ide_example.dart

import 'package:nishachar_ide/nishachar_ide.dart';

Future<void> main() async {
  // The registry needs no server at all.
  print('${NishacharClient.languages.length} languages available');
  print('.rs is ${NishacharClient.find('.rs')?.name}');

  final she = NishacharClient.find('she')!;
  print('\nStarter program for ${she.name}:\n${she.template}');

  // Everything below needs `nishachar serve` running.
  final client = NishacharClient(Uri.parse('http://localhost:8777'));
  try {
    final health = await client.health();
    print('connected to nishachar ${health['version']}');

    final result = await client.run(
      language: 'she',
      code: 'say "Hello from Dart!"',
      timeout: const Duration(seconds: 10),
    );

    print(
        'exit ${result.exitCode} in ${result.durationMs}ms via ${result.runner}');
    if (result.stdout.isNotEmpty) print(result.stdout.trimRight());
    if (result.stderr.isNotEmpty) print('stderr: ${result.stderr.trimRight()}');
  } on NishacharException catch (error) {
    print('could not run: ${error.message}');
    print('is the backend running?  nishachar serve');
  } finally {
    client.close();
  }
}
