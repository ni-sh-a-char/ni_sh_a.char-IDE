package io.github.nishachar

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class RegistryTest {

    @Test
    fun `ships every language without a server`() {
        assertTrue(NishacharClient.languages.size >= 60, "expected the full registry")
    }

    @Test
    fun `resolves by id alias extension and display name`() {
        val python = NishacharClient.find("python")
        assertNotNull(python)
        assertEquals(python, NishacharClient.find("py"))
        assertEquals(python, NishacharClient.find(".py"))
        assertEquals(python, NishacharClient.find("PY"))
        assertEquals(python, NishacharClient.find("Python"))
    }

    @Test
    fun `returns null for an unknown language`() {
        assertNull(NishacharClient.find("cobolscript"))
        assertNull(NishacharClient.find(""))
        assertNull(NishacharClient.find("   "))
    }

    @Test
    fun `SHE is present and browser capable`() {
        val she = assertNotNull(NishacharClient.find("she"))
        assertTrue(".she" in she.extensions)
        assertTrue(she.runsInBrowser)
        assertTrue(she.template.isNotEmpty())
    }

    @Test
    fun `every entry is usable`() {
        for (language in NishacharClient.languages) {
            assertTrue(language.id.isNotEmpty(), language.name)
            assertTrue(language.extensions.isNotEmpty(), language.id)
            assertTrue(language.template.isNotEmpty(), language.id)
            assertTrue(language.extensions.all { it.startsWith(".") }, language.id)
        }
    }

    @Test
    fun `ids are unique`() {
        val ids = NishacharClient.languages.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }
}

class JsonTest {

    @Test
    fun `parses the shapes the API returns`() {
        val parsed = Json.parse(
            """{"stdout":"hi\n","exitCode":0,"ok":true,"nothing":null,"list":[1,2.5,-3]}""",
        ) as Map<*, *>

        assertEquals("hi\n", parsed["stdout"])
        assertEquals(0.0, parsed["exitCode"])
        assertEquals(true, parsed["ok"])
        assertNull(parsed["nothing"])
        assertEquals(listOf(1.0, 2.5, -3.0), parsed["list"])
    }

    @Test
    fun `handles every escape sequence`() {
        val parsed = Json.parse(""" {"s":"a\"b\\c\/d\ne\tf\rg\bh\fi"} """) as Map<*, *>
        assertEquals("a\"b\\c/d\ne\tf\rg\bhi", parsed["s"])
    }

    @Test
    fun `handles unicode escapes and surrogate pairs`() {
        val parsed = Json.parse("""{"s":"é ✓ 🚀"}""") as Map<*, *>
        assertEquals("é ✓ 😀".length - 1, (parsed["s"] as String).length - 1)
        assertTrue((parsed["s"] as String).startsWith("é ✓ "))
        assertEquals("🚀", (parsed["s"] as String).substring(4))
    }

    @Test
    fun `handles raw non-ascii text`() {
        val parsed = Json.parse("""{"s":"héllo 日本 ✓"}""") as Map<*, *>
        assertEquals("héllo 日本 ✓", parsed["s"])
    }

    @Test
    fun `handles nesting and empty containers`() {
        val parsed = Json.parse("""{"a":{"b":[{"c":[]}]},"d":{},"e":[]}""") as Map<*, *>
        val a = parsed["a"] as Map<*, *>
        val b = a["b"] as List<*>
        assertEquals(emptyList<Any?>(), (b[0] as Map<*, *>)["c"])
        assertEquals(emptyMap<String, Any?>(), parsed["d"])
        assertEquals(emptyList<Any?>(), parsed["e"])
    }

    @Test
    fun `handles exponent notation`() {
        val parsed = Json.parse("""{"n":1.5e3,"m":-2E-2}""") as Map<*, *>
        assertEquals(1500.0, parsed["n"])
        assertEquals(-0.02, parsed["m"])
    }

    @Test
    fun `tolerates whitespace anywhere`() {
        val parsed = Json.parse("  {\n \"a\" :\t[ 1 , 2 ]\r\n}  ") as Map<*, *>
        assertEquals(listOf(1.0, 2.0), parsed["a"])
    }

    @Test
    fun `rejects malformed input instead of guessing`() {
        for (bad in listOf("{", "{\"a\"}", "{\"a\":}", "[1,]", "{}{}", "", "tru", "\"unterminated")) {
            assertFailsWith<IllegalArgumentException>("should reject: $bad") { Json.parse(bad) }
        }
    }

    @Test
    fun `round-trips through write and parse`() {
        val original = mapOf(
            "language" to "python",
            "code" to "print(\"quotes\\\" and \\n newlines\")\n\ttab",
            "stdin" to "héllo ✓",
            "timeout" to 5.0,
            "flag" to true,
            "nothing" to null,
        )
        val parsed = Json.parse(Json.write(original)) as Map<*, *>
        assertEquals(original["code"], parsed["code"])
        assertEquals(original["stdin"], parsed["stdin"])
        assertEquals(5.0, parsed["timeout"])
        assertEquals(true, parsed["flag"])
        assertNull(parsed["nothing"])
    }

    @Test
    fun `escapes control characters when writing`() {
        assertEquals("\"a\\u0001b\"", Json.write("ab"))
    }
}

class ClientTest {

    @Test
    fun `strips trailing slashes from the endpoint`() {
        assertEquals("http://localhost:8777", NishacharClient("http://localhost:8777///").endpoint)
        assertEquals("http://localhost:8777", NishacharClient("http://localhost:8777").endpoint)
    }

    @Test
    fun `reports an unreachable backend rather than leaking IOException`() {
        // Port 1 is reserved and never listening.
        val client = NishacharClient("http://127.0.0.1:1")
        val error = assertFailsWith<NishacharException> {
            client.run(language = "python", code = "print(1)")
        }
        assertTrue(error.message!!.contains("could not reach"), error.message!!)
    }

    @Test
    fun `exec result reports success correctly`() {
        assertTrue(ExecResult(exitCode = 0).ok)
        assertTrue(!ExecResult(exitCode = 1).ok)
        assertTrue(!ExecResult(exitCode = 0, timedOut = true).ok)
    }
}
