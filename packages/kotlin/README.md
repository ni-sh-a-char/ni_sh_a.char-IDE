# nishachar-ide (Kotlin / JVM)

**Run any language, anywhere.** A Kotlin and Java client for the
[ni_sh_a.char-IDE](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE) polyglot
execution engine — with the full **62-language registry compiled in** and
**zero runtime dependencies**.

[![Maven Central](https://img.shields.io/maven-central/v/io.github.ni-sh-a-char/nishachar-ide.svg)](https://central.sonatype.com/artifact/io.github.ni-sh-a-char/nishachar-ide)
[![License](https://img.shields.io/badge/license-Apache--2.0-D22128.svg)](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/main/LICENSE)

## Zero dependencies, deliberately

The only thing on your classpath is `kotlin-stdlib`. No Jackson, no Gson, no
kotlinx-serialization — because a client library that drags in a JSON stack
forces its version choice on every consumer, and conflicts in that layer are a
genuinely common source of pain on Android and in Spring apps.

HTTP comes from `java.net.http` in the JDK, and JSON from a small, thoroughly
tested internal reader.

## Install

**Maven**

```xml
<dependency>
  <groupId>io.github.ni-sh-a-char</groupId>
  <artifactId>nishachar-ide</artifactId>
  <version>2.0.0</version>
</dependency>
```

**Gradle**

```kotlin
implementation("io.github.ni-sh-a-char:nishachar-ide:2.0.0")
```

Requires Java 11 or newer.

## The registry needs no server

```kotlin
import io.github.nishachar.NishacharClient

NishacharClient.languages.size          // 62
NishacharClient.find(".rs")?.name       // Rust
NishacharClient.find("py")?.template    // print("Hello from Python!")

val she = NishacharClient.find("she")!!
she.runsInBrowser                       // true
```

`find` resolves by id, alias, extension or display name — `python`, `py`, `.py`
and `Python` all reach the same entry.

## Run code

Start a backend:

```bash
pip install nishachar-ide
nishachar serve
```

Then:

```kotlin
import io.github.nishachar.NishacharClient
import java.time.Duration

val client = NishacharClient("http://localhost:8777")

val result = client.run(
    language = "she",
    code = """say "Hello from Kotlin!"""",
    timeout = Duration.ofSeconds(10),
)

println(result.stdout)      // Hello from Kotlin!
println(result.exitCode)    // 0
println(result.durationMs)  // 158
println(result.runner)      // local
```

### From Java

`@JvmStatic` and `@JvmOverloads` are applied throughout, so the API is natural
from Java too:

```java
import io.github.nishachar.*;

NishacharClient client = new NishacharClient("http://localhost:8777");

System.out.println(NishacharClient.getLanguages().size());   // 62
System.out.println(NishacharClient.find(".rs").getName());   // Rust

ExecResult result = client.run("python", "print(6 * 7)");
System.out.println(result.getStdout());                      // 42
System.out.println(result.getOk());                          // true
```

### Standard input

```kotlin
client.run(
    language = "python",
    code = "print(input().uppercase())",
    stdin = "quiet\n",
)
```

### Errors

A program that exits non-zero is a **result**, not an exception — that is
normal program behaviour and you almost always want to show it:

```kotlin
val result = client.run("python", "raise SystemExit(3)")
result.ok         // false
result.exitCode   // 3
result.stderr     // the traceback
```

`NishacharException` is thrown only when the request itself fails:

```kotlin
try {
    client.run("klingon", "x")
} catch (error: NishacharException) {
    println("${error.statusCode}: ${error.message}")  // 404: unknown language 'klingon'
}
```

## Threading

`NishacharClient` is thread-safe and pools connections; create one and keep it.
`run` blocks the calling thread, so on Android call it from a coroutine
dispatcher or a background executor rather than the main thread:

```kotlin
val result = withContext(Dispatchers.IO) {
    client.run("python", source)
}
```

## Security

This library talks to a server that executes arbitrary code. Point it only at a
backend you control, and read
[SECURITY.md](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/main/SECURITY.md)
before exposing one — the server's default local runner has **no isolation**,
and `--runner docker` exists for untrusted input.

## Links

- [Live demo](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/) — runs SHE and Python in your browser, no backend
- [Documentation](https://ni-sh-a-char.github.io/ni_sh_a.char-IDE/docs/)
- [Repository](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE)
- [Add a language](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/blob/v2.0.0/languages/README.md) — 8 lines of JSON

Apache-2.0 © Piyush Mishra
