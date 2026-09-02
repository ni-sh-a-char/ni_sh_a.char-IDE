import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nishachar_ide/nishachar_ide.dart';
import 'package:test/test.dart';

/// A stub backend, so these tests never need a running server.
http.Client stubbing(
  Object? body, {
  int status = 200,
  void Function(http.Request request)? inspect,
}) =>
    MockClient((request) async {
      inspect?.call(request);
      return http.Response(
        jsonEncode(body),
        status,
        headers: const {'content-type': 'application/json; charset=utf-8'},
      );
    });

void main() {
  group('registry', () {
    test('ships every language without a server', () {
      expect(kLanguages.length, greaterThanOrEqualTo(60));
      expect(NishacharClient.languages, same(kLanguages));
    });

    test('resolves by id, alias, extension and display name', () {
      final python = NishacharClient.find('python');
      expect(python, isNotNull);
      expect(NishacharClient.find('py'), python);
      expect(NishacharClient.find('.py'), python);
      expect(NishacharClient.find('PY'), python);
      expect(NishacharClient.find('Python'), python);
    });

    test('returns null for an unknown language', () {
      expect(NishacharClient.find('cobolscript'), isNull);
      expect(NishacharClient.find(''), isNull);
    });

    test('SHE is present and marked as browser-capable', () {
      final she = NishacharClient.find('she');
      expect(she, isNotNull);
      expect(she!.extensions, contains('.she'));
      expect(she.runsInBrowser, isTrue);
      expect(she.template, isNotEmpty);
    });

    test('every entry is usable', () {
      for (final language in kLanguages) {
        expect(language.id, isNotEmpty, reason: language.name);
        expect(language.extensions, isNotEmpty, reason: language.id);
        expect(language.template, isNotEmpty, reason: language.id);
        expect(language.extensions.every((e) => e.startsWith('.')), isTrue,
            reason: language.id);
      }
    });

    test('ids are unique', () {
      final ids = kLanguages.map((l) => l.id).toList();
      expect(ids.toSet().length, ids.length);
    });
  });

  group('run', () {
    test('returns the program output', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing({
          'stdout': 'hello\n',
          'stderr': '',
          'exitCode': 0,
          'durationMs': 42,
          'timedOut': false,
          'truncated': false,
          'language': 'she',
          'runner': 'local',
        }),
      );

      final result = await client.run(language: 'she', code: 'say "hello"');
      expect(result.stdout, 'hello\n');
      expect(result.exitCode, 0);
      expect(result.ok, isTrue);
      expect(result.durationMs, 42);
      expect(result.runner, 'local');
    });

    test('sends the documented payload', () async {
      Map<String, dynamic>? sent;
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing(
          {'stdout': '', 'exitCode': 0},
          inspect: (request) =>
              sent = jsonDecode(request.body) as Map<String, dynamic>,
        ),
      );

      await client.run(
        language: 'python',
        code: 'print(1)',
        stdin: 'in',
        timeout: const Duration(seconds: 5),
      );

      expect(sent!['language'], 'python');
      expect(sent!['code'], 'print(1)');
      expect(sent!['stdin'], 'in');
      expect(sent!['timeout'], 5.0);
    });

    test('a non-zero exit is a result, not an exception', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing({'stdout': '', 'stderr': 'boom', 'exitCode': 1}),
      );

      final result = await client.run(language: 'py', code: 'x');
      expect(result.ok, isFalse);
      expect(result.exitCode, 1);
      expect(result.stderr, 'boom');
    });

    test('surfaces the server error message', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient:
            stubbing({'error': "unknown language 'klingon'"}, status: 404),
      );

      expect(
        () => client.run(language: 'klingon', code: 'x'),
        throwsA(isA<NishacharException>()
            .having((e) => e.statusCode, 'statusCode', 404)
            .having((e) => e.message, 'message', contains('klingon'))),
      );
    });

    test('reports an unreachable backend', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:9'),
        httpClient:
            MockClient((_) async => throw http.ClientException('refused')),
      );

      expect(
        () => client.run(language: 'py', code: 'x'),
        throwsA(isA<NishacharException>()
            .having((e) => e.message, 'message', contains('could not reach'))),
      );
    });

    test('decodes non-ASCII output correctly', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing({'stdout': 'héllo ✓ 日本\n', 'exitCode': 0}),
      );

      final result = await client.run(language: 'py', code: 'x');
      expect(result.stdout, 'héllo ✓ 日本\n');
    });

    test('flags a run killed by the time limit', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing({'exitCode': 124, 'timedOut': true}),
      );

      final result = await client.run(language: 'py', code: 'while True: pass');
      expect(result.timedOut, isTrue);
      expect(result.ok, isFalse);
    });
  });

  group('endpoint handling', () {
    test('strips trailing slashes', () {
      expect(
        NishacharClient(Uri.parse('http://localhost:8777///'))
            .endpoint
            .toString(),
        'http://localhost:8777',
      );
    });

    test('preserves a base path', () async {
      String? path;
      final client = NishacharClient(
        Uri.parse('http://localhost/ide/'),
        httpClient: stubbing(
          {'exitCode': 0},
          inspect: (request) => path = request.url.path,
        ),
      );

      await client.run(language: 'py', code: 'x');
      expect(path, '/ide/api/run');
    });
  });

  group('languages endpoint', () {
    test('parses the server list', () async {
      final client = NishacharClient(
        Uri.parse('http://localhost:8777'),
        httpClient: stubbing({
          'count': 1,
          'languages': [
            {
              'id': 'python',
              'name': 'Python',
              'extensions': ['.py']
            },
          ],
        }),
      );

      final languages = await client.fetchLanguages();
      expect(languages.single.id, 'python');
      expect(languages.single.extensions, ['.py']);
    });
  });
}
