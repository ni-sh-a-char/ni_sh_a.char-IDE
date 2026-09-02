package io.github.nishachar

/**
 * A minimal JSON reader, so this library has zero runtime dependencies.
 *
 * A client library that drags in Jackson or kotlinx-serialization forces its
 * version choice on every consumer, and conflicts in that layer are a common
 * source of pain on Android and in Spring apps. The API this talks to returns
 * small, well-known documents, so a scoped parser is the cheaper trade -- but
 * it is a real parser, not a regex: it handles nesting, every escape sequence,
 * surrogate pairs and the numeric forms JSON allows.
 *
 * Deliberately not a general-purpose JSON library, and not part of the public
 * API.
 */
internal object Json {

    /** Parses a complete document. Returns Map, List, String, Double, Boolean or null. */
    fun parse(text: String): Any? {
        val reader = Reader(text)
        reader.skipWhitespace()
        val value = reader.readValue()
        reader.skipWhitespace()
        if (!reader.atEnd) reader.fail("trailing content")
        return value
    }

    /** Serialises a value. Only the shapes this client sends are supported. */
    fun write(value: Any?): String = buildString { writeTo(this, value) }

    private fun writeTo(out: StringBuilder, value: Any?) {
        when (value) {
            null -> out.append("null")
            is String -> writeString(out, value)
            is Boolean -> out.append(value)
            is Number -> out.append(value)
            is Map<*, *> -> {
                out.append('{')
                var first = true
                for ((key, entry) in value) {
                    if (!first) out.append(',')
                    first = false
                    writeString(out, key.toString())
                    out.append(':')
                    writeTo(out, entry)
                }
                out.append('}')
            }
            is Iterable<*> -> {
                out.append('[')
                var first = true
                for (entry in value) {
                    if (!first) out.append(',')
                    first = false
                    writeTo(out, entry)
                }
                out.append(']')
            }
            else -> writeString(out, value.toString())
        }
    }

    private fun writeString(out: StringBuilder, text: String) {
        out.append('"')
        for (ch in text) {
            when {
                ch == '"' -> out.append("\\\"")
                ch == '\\' -> out.append("\\\\")
                ch == '\n' -> out.append("\\n")
                ch == '\r' -> out.append("\\r")
                ch == '\t' -> out.append("\\t")
                ch == '\b' -> out.append("\\b")
                ch == '' -> out.append("\\f")
                // JSON forbids raw control characters.
                ch < ' ' -> out.append("\\u%04x".format(ch.code))
                else -> out.append(ch)
            }
        }
        out.append('"')
    }

    private class Reader(private val text: String) {
        private var index = 0

        val atEnd: Boolean get() = index >= text.length

        fun fail(reason: String): Nothing =
            throw IllegalArgumentException("invalid JSON at offset $index: $reason")

        fun skipWhitespace() {
            while (index < text.length && text[index].isJsonWhitespace()) index++
        }

        fun readValue(): Any? {
            if (atEnd) fail("unexpected end of input")
            return when (text[index]) {
                '{' -> readObject()
                '[' -> readArray()
                '"' -> readString()
                't' -> readLiteral("true", true)
                'f' -> readLiteral("false", false)
                'n' -> readLiteral("null", null)
                else -> readNumber()
            }
        }

        private fun readObject(): Map<String, Any?> {
            index++ // consume '{'
            val result = LinkedHashMap<String, Any?>()
            skipWhitespace()
            if (!atEnd && text[index] == '}') {
                index++
                return result
            }
            while (true) {
                skipWhitespace()
                if (atEnd || text[index] != '"') fail("expected a key")
                val key = readString()
                skipWhitespace()
                if (atEnd || text[index] != ':') fail("expected ':'")
                index++
                skipWhitespace()
                result[key] = readValue()
                skipWhitespace()
                if (atEnd) fail("unterminated object")
                when (text[index]) {
                    ',' -> index++
                    '}' -> {
                        index++
                        return result
                    }
                    else -> fail("expected ',' or '}'")
                }
            }
        }

        private fun readArray(): List<Any?> {
            index++ // consume '['
            val result = ArrayList<Any?>()
            skipWhitespace()
            if (!atEnd && text[index] == ']') {
                index++
                return result
            }
            while (true) {
                skipWhitespace()
                result.add(readValue())
                skipWhitespace()
                if (atEnd) fail("unterminated array")
                when (text[index]) {
                    ',' -> index++
                    ']' -> {
                        index++
                        return result
                    }
                    else -> fail("expected ',' or ']'")
                }
            }
        }

        private fun readString(): String {
            index++ // consume opening quote
            val out = StringBuilder()
            while (true) {
                if (atEnd) fail("unterminated string")
                when (val ch = text[index++]) {
                    '"' -> return out.toString()
                    '\\' -> out.append(readEscape())
                    else -> out.append(ch)
                }
            }
        }

        private fun readEscape(): Char {
            if (atEnd) fail("unterminated escape")
            return when (val ch = text[index++]) {
                '"', '\\', '/' -> ch
                'n' -> '\n'
                't' -> '\t'
                'r' -> '\r'
                'b' -> '\b'
                'f' -> ''
                'u' -> {
                    if (index + 4 > text.length) fail("truncated \\u escape")
                    val hex = text.substring(index, index + 4)
                    index += 4
                    // A surrogate pair arrives as two \u escapes; appending each
                    // char separately reassembles it correctly in a String.
                    val code = hex.toIntOrNull(16) ?: fail("bad \\u escape")
                    code.toChar()
                }
                else -> fail("unknown escape")
            }
        }

        private fun readNumber(): Double {
            val start = index
            if (!atEnd && (text[index] == '-' || text[index] == '+')) index++
            while (!atEnd && (text[index].isDigit() || text[index] in ".eE+-")) index++
            if (start == index) fail("expected a value")
            return text.substring(start, index).toDoubleOrNull() ?: fail("bad number")
        }

        private fun <T> readLiteral(word: String, value: T): T {
            if (!text.startsWith(word, index)) fail("expected '$word'")
            index += word.length
            return value
        }

        private fun Char.isJsonWhitespace() =
            this == ' ' || this == '\t' || this == '\n' || this == '\r'
    }
}
