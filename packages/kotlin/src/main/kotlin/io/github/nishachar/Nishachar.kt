package io.github.nishachar

import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets
import java.time.Duration

/**
 * A language the IDE knows how to run.
 *
 * Entries come from the JSON registry in the repository and are
 * generated into [LANGUAGES]. See `languages/` and tools/generate_bindings.py.
 */
public data class Language(
    /** Unique lowercase identifier, for example `python`. */
    public val id: String,
    /** Display name, for example `C++`. */
    public val name: String,
    /** Alternative names a user might type, for example `py`. */
    public val aliases: List<String> = emptyList(),
    /** File extensions, each including the leading dot. */
    public val extensions: List<String> = emptyList(),
    /** Line-comment prefix, useful for a comment-toggle command. */
    public val comment: String = "#",
    /** Syntax highlighting mode identifier used by the web component. */
    public val highlight: String = "text",
    /** A hello-world program, suitable as a starting buffer. */
    public val template: String = "",
    /** The language's official homepage. */
    public val website: String = "",
    /** In-browser engine (`pyodide` or `native`), or empty if it needs a backend. */
    public val browser: String = "",
    /** Whether running this language involves a separate compile step. */
    public val compiled: Boolean = false,
) {
    /** Whether this language can run with no backend at all. */
    public val runsInBrowser: Boolean get() = browser.isNotEmpty()

    /**
     * Whether [query] names this language.
     *
     * Accepts the id, an alias, an extension with or without its dot, or the
     * display name, case-insensitively: `python`, `py`, `.py` and `Python` all
     * match the same entry.
     */
    public fun matches(query: String): Boolean {
        val key = query.trim().lowercase()
        if (key.isEmpty()) return false
        if (key == id || key == name.lowercase()) return true
        if (key in aliases) return true
        return key in extensions || ".$key" in extensions
    }
}

/**
 * The outcome of running a program. Identical in shape across every client.
 */
public data class ExecResult(
    /** Everything the program wrote to standard output. */
    public val stdout: String = "",
    /** Everything the program wrote to standard error. */
    public val stderr: String = "",
    /** The program's exit code. 124 means it was killed for exceeding its limit. */
    public val exitCode: Int = 0,
    /** Wall-clock time the run took, in milliseconds. */
    public val durationMs: Long = 0,
    /** Whether the run was killed for exceeding its time limit. */
    public val timedOut: Boolean = false,
    /** Whether output was cut short by the server's byte cap. */
    public val truncated: Boolean = false,
    /** The language that was run. */
    public val language: String = "",
    /** Which backend executed it: `local`, `docker` or `browser`. */
    public val runner: String = "",
) {
    /** Whether the program finished successfully. */
    public val ok: Boolean get() = exitCode == 0 && !timedOut
}

/** Thrown when the server refuses a request or cannot be reached. */
public class NishacharException(
    message: String,
    /** The HTTP status code, when the failure came from the server. */
    public val statusCode: Int? = null,
    cause: Throwable? = null,
) : RuntimeException(message, cause)

/**
 * A client for a `nishachar serve` backend.
 *
 * ```kotlin
 * val client = NishacharClient("http://localhost:8777")
 * val result = client.run(language = "she", code = "say \"hi\"")
 * println(result.stdout)
 * ```
 *
 * Instances are thread-safe and cheap to keep around; the underlying
 * [HttpClient] pools connections.
 */
public class NishacharClient
@JvmOverloads
constructor(
    endpoint: String,
    private val http: HttpClient =
        HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build(),
    private val requestTimeout: Duration = Duration.ofSeconds(130),
) {
    /** The base URL of the backend, without a trailing slash. */
    public val endpoint: String = endpoint.trimEnd('/')

    public companion object {
        /**
         * Every language in the registry, without contacting a server.
         *
         * Compiled into the library, so it works offline and before any
         * backend is reachable.
         */
        @JvmStatic
        public val languages: List<Language> get() = LANGUAGES

        /**
         * Finds a language by id, alias, extension or display name, or `null`.
         */
        @JvmStatic
        public fun find(name: String): Language? = LANGUAGES.firstOrNull { it.matches(name) }
    }

    /** Reports the server's version, active runner and language count. */
    public fun health(): Map<String, Any?> = getObject("/api/health")

    /** Asks the server which languages it can run. */
    public fun fetchLanguages(): List<Language> {
        val body = getObject("/api/languages")
        val entries = body["languages"] as? List<*>
            ?: throw NishacharException("malformed /api/languages response")
        return entries.filterIsInstance<Map<*, *>>().map { it.toLanguage() }
    }

    /**
     * Runs [code] as [language] and returns the result.
     *
     * [language] accepts an id, alias or extension. [stdin] is fed to the
     * program's standard input. [timeout] is the server-side limit; the server
     * clamps it to its own maximum.
     *
     * A program that merely exits non-zero is a normal result. This throws
     * [NishacharException] only when the request itself fails: an unknown
     * language, a rejected request, or an unreachable backend.
     */
    @JvmOverloads
    public fun run(
        language: String,
        code: String,
        stdin: String = "",
        timeout: Duration? = null,
    ): ExecResult {
        val payload = buildMap<String, Any?> {
            put("language", language)
            put("code", code)
            put("stdin", stdin)
            if (timeout != null) put("timeout", timeout.toMillis() / 1000.0)
        }

        val request = newRequest("/api/run")
            .header("content-type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(Json.write(payload), StandardCharsets.UTF_8))
            .build()

        val response = send(request)
        val body = decode(response.body())

        if (response.statusCode() >= 400) {
            val message = (body as? Map<*, *>)?.get("error") as? String
                ?: "server returned ${response.statusCode()}"
            throw NishacharException(message, response.statusCode())
        }
        val fields = body as? Map<*, *>
            ?: throw NishacharException("malformed /api/run response")

        return ExecResult(
            stdout = fields.string("stdout"),
            stderr = fields.string("stderr"),
            exitCode = fields.int("exitCode"),
            durationMs = fields.int("durationMs").toLong(),
            timedOut = fields["timedOut"] as? Boolean ?: false,
            truncated = fields["truncated"] as? Boolean ?: false,
            language = fields.string("language"),
            runner = fields.string("runner"),
        )
    }

    // -- plumbing ---------------------------------------------------------

    private fun newRequest(path: String): HttpRequest.Builder =
        HttpRequest.newBuilder(URI.create("$endpoint$path")).timeout(requestTimeout)

    private fun send(request: HttpRequest): HttpResponse<ByteArray> =
        try {
            http.send(request, HttpResponse.BodyHandlers.ofByteArray())
        } catch (error: IOException) {
            throw NishacharException("could not reach $endpoint: ${error.message}", null, error)
        } catch (error: InterruptedException) {
            Thread.currentThread().interrupt()
            throw NishacharException("interrupted while calling $endpoint", null, error)
        }

    private fun getObject(path: String): Map<String, Any?> {
        val response = send(newRequest(path).GET().build())
        if (response.statusCode() >= 400) {
            throw NishacharException(
                "server returned ${response.statusCode()}",
                response.statusCode(),
            )
        }
        @Suppress("UNCHECKED_CAST")
        return decode(response.body()) as? Map<String, Any?>
            ?: throw NishacharException("malformed response from $path")
    }

    /** Always UTF-8: program output is arbitrary text, including non-ASCII. */
    private fun decode(body: ByteArray): Any? =
        try {
            Json.parse(String(body, StandardCharsets.UTF_8))
        } catch (error: IllegalArgumentException) {
            throw NishacharException("server sent malformed JSON: ${error.message}", null, error)
        }
}

private fun Map<*, *>.string(key: String): String = this[key] as? String ?: ""

/** JSON has one number type, so integers arrive as doubles. */
private fun Map<*, *>.int(key: String): Int = (this[key] as? Number)?.toInt() ?: 0

private fun Map<*, *>.toLanguage(): Language = Language(
    id = string("id"),
    name = string("name"),
    aliases = (this["aliases"] as? List<*>)?.filterIsInstance<String>() ?: emptyList(),
    extensions = (this["extensions"] as? List<*>)?.filterIsInstance<String>() ?: emptyList(),
    comment = this["comment"] as? String ?: "#",
    highlight = this["highlight"] as? String ?: "text",
    template = string("template"),
    website = string("website"),
    browser = string("browser"),
    compiled = this["compiled"] as? Boolean ?: false,
)
