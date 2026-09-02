# Security Policy

This project's entire purpose is to execute arbitrary code. That makes the
threat model unusually important, so this document states plainly what each
part protects against — and what it does not.

## Reporting a vulnerability

Report privately through
[GitHub Security Advisories](https://github.com/ni-sh-a-char/ni_sh_a.char-IDE/security/advisories/new),
or email **piyushmishra.professional@gmail.com**.

Please do not open a public issue for a vulnerability.

Expect an acknowledgement within 72 hours and an assessment within 7 days.
Fixes for confirmed issues ship as a patch release, and you will be credited
in the advisory unless you prefer otherwise.

## Supported versions

| Version | Supported |
|:--|:--|
| 2.x | ✅ |
| 1.x | ❌ (single-file Tkinter prototype, superseded) |

## The three tiers, and what each guarantees

### Tier 0 — browser (WebAssembly)

Code runs in the visitor's own tab, inside the browser's sandbox.

**Protects against:** touching the host filesystem, the network, or anything
outside the tab. Pyodide's virtual filesystem is in-memory and disappears with
the page. JavaScript runs in a Worker that can be terminated.

**Does not protect against:** consuming the visitor's own CPU and memory. A
hostile snippet can make the tab slow. It cannot escape it.

### Tier 1 — local

Code runs as a subprocess, **as you, with your privileges, with no isolation**.

**Protects against:** hanging forever (wall-clock timeout), flooding memory
with output (per-stream byte cap), and orphaned processes (the whole process
tree is killed on timeout).

**Does not protect against:** anything else. A program run on this tier can
read your files, delete them, and open network connections. This is the right
behaviour for code you wrote and wrong for code you did not.

Never point a Tier 1 server at input from people you do not trust.

### Tier 2 — Docker

Code runs in a disposable container started with:

| Flag | Effect |
|:--|:--|
| `--network none` | no network access of any kind |
| `--read-only` | root filesystem cannot be written |
| `--cap-drop ALL` | every Linux capability dropped |
| `--security-opt no-new-privileges` | no privilege escalation via setuid |
| `--memory 256m` / `--memory-swap 256m` | hard memory ceiling, no swap escape |
| `--cpus 1.0` | CPU ceiling |
| `--pids-limit 128` | fork bombs cannot exhaust the process table |
| `--rm` | container and its writes are destroyed after the run |

Languages needing packages install them at **image build time**, when the
network is still up. By the time your code runs, there is no network.

**Does not protect against:** kernel-level container escapes. Containers share
a kernel; a sufficiently severe kernel vulnerability defeats them. For
genuinely hostile input at scale, put a VM boundary underneath.

## Server trust boundaries

`nishachar serve` defaults are deliberately restrictive.

- **Unsandboxed execution is refused off localhost.** Serving the local runner
  on a non-loopback address is a remote shell; the server will not start
  without `--runner docker` or an explicit `--allow-remote-exec`.
- **CORS is closed.** An open `Access-Control-Allow-Origin` on a localhost
  server would let any page you visit execute code on your machine. Embedding
  from another origin is opt-in per origin, via `--cors`.
- **The `Host` header is validated** on loopback binds. Without this, a hostile
  site can point its own domain at `127.0.0.1` and talk to your local server
  from its own origin — DNS rebinding. The check is skipped when you bind to a
  public address, since you have then chosen exposure and the hostname is
  unpredictable.
- **The terminal is off.** `/api/pty` returns a refusal unless you pass
  `--allow-shell`. It grants a full interactive shell; that should be a
  decision, not a default.
- **Requests are bounded.** Source is capped at 1 MiB, timeouts at 120s.

## Known limitations

Stated up front rather than discovered later:

1. **Tier 1 offers no isolation.** By design. Use Tier 2 for untrusted code.
2. **The Docker runner has not been exercised end-to-end in this
   repository's own CI on every platform.** Its flag construction is unit
   tested; container behaviour is verified by the Linux integration job.
3. **Container escape is out of scope.** See above.
4. **`--allow-shell` is exactly as dangerous as it sounds.** It is a shell.
5. **Registry definitions are trusted input.** A malicious `languages/*.json`
   in a fork could run an arbitrary command. Review language PRs like any other
   code — the argument vectors are the executable part.

## Hardening a public deployment

If you expose this to people you do not trust:

```bash
nishachar serve \
  --host 0.0.0.0 \
  --runner docker \        # never 'local'
  --timeout 10 \
  --cors https://your-site.example
# Terminal stays off. Put it behind a reverse proxy with rate limiting,
# and run the whole thing in a VM.
```
