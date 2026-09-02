/// A language the IDE knows how to run.
///
/// Entries come from the registry at `languages/*.json` in the repository and
/// are generated into [kLanguages] -- see `tools/generate_bindings.py`.
class Language {
  /// Creates a language definition.
  const Language({
    required this.id,
    required this.name,
    required this.aliases,
    required this.extensions,
    required this.comment,
    required this.highlight,
    required this.template,
    required this.website,
    required this.browser,
    required this.compiled,
  });

  /// Builds a language from the JSON returned by `GET /api/languages`.
  factory Language.fromJson(Map<String, dynamic> json) => Language(
        id: json['id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        aliases: _strings(json['aliases']),
        extensions: _strings(json['extensions']),
        comment: json['comment'] as String? ?? '#',
        highlight: json['highlight'] as String? ?? 'text',
        template: json['template'] as String? ?? '',
        website: json['website'] as String? ?? '',
        browser: json['browser'] as String? ?? '',
        compiled: json['compiled'] as bool? ?? false,
      );

  /// Unique lowercase identifier, for example `python`.
  final String id;

  /// Display name, for example `C++`.
  final String name;

  /// Alternative names a user might type, for example `py`.
  final List<String> aliases;

  /// File extensions, each including the leading dot.
  final List<String> extensions;

  /// Line-comment prefix, useful for a comment-toggle command.
  final String comment;

  /// Syntax highlighting mode identifier used by the web component.
  final String highlight;

  /// A hello-world program, suitable as a starting buffer.
  final String template;

  /// The language's official homepage.
  final String website;

  /// In-browser engine (`pyodide` or `native`), or empty if it needs a backend.
  final String browser;

  /// Whether running this language involves a separate compile step.
  final bool compiled;

  /// Whether this language can run with no backend at all.
  bool get runsInBrowser => browser.isNotEmpty;

  /// Whether [name] matches this language's id, an alias, or an extension.
  ///
  /// Accepts `python`, `py`, `.py` and `Python` alike.
  bool matches(String name) {
    final key = name.trim().toLowerCase();
    if (key.isEmpty) return false;
    if (key == id || key == this.name.toLowerCase()) return true;
    if (aliases.contains(key)) return true;
    return extensions.contains(key) || extensions.contains('.$key');
  }

  @override
  String toString() => 'Language($id)';

  @override
  bool operator ==(Object other) => other is Language && other.id == id;

  @override
  int get hashCode => id.hashCode;
}

List<String> _strings(Object? value) => value is List
    ? value.whereType<String>().toList(growable: false)
    : const <String>[];
