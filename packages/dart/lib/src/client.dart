import 'dart:convert';

import 'package:http/http.dart' as http;

import 'language.dart';
import 'registry.g.dart';

/// The outcome of running a program. Identical in shape across every client.
class ExecResult {
  /// Creates a result.
  const ExecResult({
    required this.stdout,
    required this.stderr,
    required this.exitCode,
    required this.durationMs,
    required this.timedOut,
    required this.truncated,
    required this.language,
    required this.runner,
  });

  /// Parses the JSON body returned by `POST /api/run`.
  factory ExecResult.fromJson(Map<String, dynamic> json) => ExecResult(
        stdout: json['stdout'] as String? ?? '',
        stderr: json['stderr'] as String? ?? '',
        exitCode: (json['exitCode'] as num?)?.toInt() ?? 0,
        durationMs: (json['durationMs'] as num?)?.toInt() ?? 0,
        timedOut: json['timedOut'] as bool? ?? false,
        truncated: json['truncated'] as bool? ?? false,
        language: json['language'] as String? ?? '',
        runner: json['runner'] as String? ?? '',
      );

  /// Everything the program wrote to standard output.
  final String stdout;

  /// Everything the program wrote to standard error.
  final String stderr;

  /// The program's exit code. 124 means it was killed for exceeding its limit.
  final int exitCode;

  /// Wall-clock time the run took, in milliseconds.
  final int durationMs;

  /// Whether the run was killed for exceeding its time limit.
  final bool timedOut;

  /// Whether output was cut short by the server's byte cap.
  final bool truncated;

  /// The language that was run.
  final String language;

  /// Which backend executed it: `local`, `docker` or `browser`.
  final String runner;

  /// Whether the program finished successfully.
  bool get ok => exitCode == 0 && !timedOut;

  @override
  String toString() => 'ExecResult(exit $exitCode in ${durationMs}ms)';
}

/// Thrown when the server refuses a request or cannot be reached.
class NishacharException implements Exception {
  /// Creates an exception with a [message] and optional HTTP [statusCode].
  const NishacharException(this.message, [this.statusCode]);

  /// Human-readable explanation.
  final String message;

  /// The HTTP status code, when the failure came from the server.
  final int? statusCode;

  @override
  String toString() => statusCode == null
      ? 'NishacharException: $message'
      : 'NishacharException($statusCode): $message';
}

/// A client for a `nishachar serve` backend.
///
/// ```dart
/// final client = NishacharClient(Uri.parse('http://localhost:8777'));
/// final result = await client.run(language: 'she', code: 'say "hi"');
/// print(result.stdout);
/// client.close();
/// ```
class NishacharClient {
  /// Creates a client pointed at [endpoint].
  ///
  /// Pass [httpClient] to reuse an existing connection pool or to inject a
  /// mock in tests. A client created internally is closed by [close].
  NishacharClient(Uri endpoint, {http.Client? httpClient})
      : endpoint = _normalise(endpoint),
        _http = httpClient ?? http.Client(),
        _ownsHttp = httpClient == null;

  /// The base URL of the backend, without a trailing slash.
  final Uri endpoint;

  final http.Client _http;
  final bool _ownsHttp;

  static Uri _normalise(Uri uri) {
    final path = uri.path.replaceAll(RegExp(r'/+$'), '');
    return uri.replace(path: path);
  }

  Uri _url(String path) => endpoint.replace(path: '${endpoint.path}$path');

  /// Every language in the registry, without contacting a server.
  ///
  /// The list is compiled in, so it works offline and before any backend is
  /// reachable. Use [fetchLanguages] for what a specific server supports.
  static List<Language> get languages => kLanguages;

  /// Finds a language by id, alias, extension or display name.
  ///
  /// `python`, `py`, `.py` and `Python` all resolve to the same entry.
  /// Returns `null` when nothing matches.
  static Language? find(String name) {
    for (final language in kLanguages) {
      if (language.matches(name)) return language;
    }
    return null;
  }

  /// Reports the server's version, active runner and language count.
  Future<Map<String, dynamic>> health() async =>
      await _getJson('/api/health') as Map<String, dynamic>;

  /// Asks the server which languages it can run.
  Future<List<Language>> fetchLanguages() async {
    final body = await _getJson('/api/languages') as Map<String, dynamic>;
    final entries = body['languages'];
    if (entries is! List) {
      throw const NishacharException('malformed /api/languages response');
    }
    return entries
        .whereType<Map<String, dynamic>>()
        .map(Language.fromJson)
        .toList(growable: false);
  }

  /// Runs [code] as [language] and returns the result.
  ///
  /// [language] accepts an id, alias or extension. [stdin] is fed to the
  /// program's standard input. [timeout] is the server-side limit in seconds;
  /// the server clamps it to its own maximum.
  ///
  /// Throws [NishacharException] if the language is unknown to the server, the
  /// request is rejected, or the backend cannot be reached. A program that
  /// merely exits non-zero is a normal result, not an exception.
  Future<ExecResult> run({
    required String language,
    required String code,
    String stdin = '',
    Duration? timeout,
  }) async {
    final payload = <String, dynamic>{
      'language': language,
      'code': code,
      'stdin': stdin,
      if (timeout != null) 'timeout': timeout.inMilliseconds / 1000.0,
    };

    late final http.Response response;
    try {
      response = await _http.post(
        _url('/api/run'),
        headers: const {'content-type': 'application/json'},
        body: jsonEncode(payload),
      );
    } on Exception catch (error) {
      throw NishacharException('could not reach $endpoint: $error');
    }

    final decoded = _decode(response);
    if (response.statusCode >= 400) {
      final message = decoded is Map && decoded['error'] is String
          ? decoded['error'] as String
          : 'server returned ${response.statusCode}';
      throw NishacharException(message, response.statusCode);
    }
    if (decoded is! Map<String, dynamic>) {
      throw const NishacharException('malformed /api/run response');
    }
    return ExecResult.fromJson(decoded);
  }

  Future<Object?> _getJson(String path) async {
    late final http.Response response;
    try {
      response = await _http.get(_url(path));
    } on Exception catch (error) {
      throw NishacharException('could not reach $endpoint: $error');
    }
    if (response.statusCode >= 400) {
      throw NishacharException(
        'server returned ${response.statusCode}',
        response.statusCode,
      );
    }
    return _decode(response);
  }

  Object? _decode(http.Response response) {
    try {
      // Always decode as UTF-8: program output is arbitrary text, and the
      // default latin-1 fallback would mangle anything non-ASCII.
      return jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      return null;
    }
  }

  /// Releases the underlying HTTP connection pool.
  ///
  /// Only closes the client if this instance created it.
  void close() {
    if (_ownsHttp) _http.close();
  }
}
