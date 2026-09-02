"""Execution behaviour: the guarantees every backend has to keep."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

import nishachar
from nishachar.registry import Language, registry
from nishachar.runners import ExecutionError, LocalRunner, get_runner
from nishachar.runners.base import clamp
from nishachar.runners.docker import DockerRunner

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


# -- output handling ------------------------------------------------------


def test_clamp_passes_short_output_through():
    text, truncated = clamp(b"hello", 1024)
    assert (text, truncated) == ("hello", False)


def test_clamp_truncates_and_says_so():
    text, truncated = clamp(b"x" * 5000, 100)
    assert truncated
    assert text.startswith("x" * 100)
    assert "truncated" in text
    assert "4900 more bytes" in text


def test_clamp_normalises_windows_line_endings():
    """Identical programs must produce identical output on every platform."""
    text, _ = clamp(b"a\r\nb\r\n", 1024)
    assert text == "a\nb\n"


def test_clamp_survives_invalid_utf8():
    text, _ = clamp(b"ok \xff\xfe", 1024)
    assert text.startswith("ok ")


# -- the local runner -----------------------------------------------------


def test_runs_python_and_captures_stdout():
    result = nishachar.run('print("hello")', "python")
    assert result.stdout == "hello\n"
    assert result.exit_code == 0
    assert result.ok
    assert result.runner == "local"


def test_reports_a_nonzero_exit_code():
    result = nishachar.run("import sys; sys.exit(3)", "py")
    assert result.exit_code == 3
    assert not result.ok


def test_captures_stderr_separately():
    result = nishachar.run('import sys; sys.stderr.write("bad\\n")', "py")
    assert result.stderr == "bad\n"
    assert result.stdout == ""


def test_stdin_is_delivered():
    result = nishachar.run("print(input().upper())", "py", stdin="quiet\n")
    assert result.stdout == "QUIET\n"


def test_a_runaway_program_is_killed():
    result = nishachar.run("while True: pass", "py", timeout=1.0)
    assert result.timed_out
    assert result.exit_code == 124
    assert "time limit" in result.stderr


def test_output_is_capped():
    result = nishachar.run('print("z" * 200000)', "py", output_limit=2048)
    assert result.truncated
    assert len(result.stdout) < 4096


def test_she_runs_end_to_end():
    """SHE is the project's flagship integration; it has to actually work."""
    pytest.importorskip("she", reason="she-lang not installed")
    result = nishachar.run('say "hi from she"', "she")
    assert result.exit_code == 0
    assert "hi from she" in result.stdout


@needs_node
def test_javascript_runs_end_to_end():
    result = nishachar.run('console.log(6 * 7)', "js")
    assert result.stdout.strip() == "42"


def test_run_file_infers_the_language(tmp_path: Path):
    script = tmp_path / "demo.py"
    script.write_text('print("from a file")', encoding="utf-8")
    assert nishachar.run_file(script).stdout == "from a file\n"


def test_run_file_rejects_an_unknown_extension(tmp_path: Path):
    mystery = tmp_path / "thing.qqq"
    mystery.write_text("?", encoding="utf-8")
    with pytest.raises(ExecutionError, match="Could not tell what language"):
        nishachar.run_file(mystery)


def test_missing_toolchain_explains_itself():
    absent = Language(id="ghost", name="Ghost", extensions=(".gh",), run=("definitely-not-installed",))
    with pytest.raises(ExecutionError, match="not installed or not on PATH"):
        LocalRunner().run("x", absent)


def test_supports_reports_toolchain_presence():
    runner = LocalRunner()
    assert runner.supports(registry.require("python"))
    ghost = Language(id="g", name="G", extensions=(".g",), run=("definitely-not-installed",))
    assert not runner.supports(ghost)


def test_compile_step_failure_is_reported_as_such():
    """A broken compile must be distinguishable from a program that ran and failed."""
    language = Language(
        id="fake",
        name="Fake",
        extensions=(".fake",),
        compile=(("definitely-not-a-compiler", "{file}"),),
        run=("{bin}",),
    )
    with pytest.raises(ExecutionError):
        LocalRunner().run("code", language)


def test_workspace_is_cleaned_up(tmp_path: Path):
    runner = LocalRunner(workdir=tmp_path)
    runner.run('print("x")', registry.require("python"))
    assert list(tmp_path.iterdir()) == []


def test_source_filename_override_is_honoured(tmp_path: Path):
    """Java refuses to run unless the file is named after its public class."""
    language = Language(
        id="named",
        name="Named",
        extensions=(".txt",),
        filename="Main.java",
        run=(sys.executable, "-c", "import os;print(os.path.basename(r'{file}'))"),
    )
    result = LocalRunner(workdir=tmp_path).run("x", language)
    assert result.stdout.strip() == "Main.java"


# -- the docker runner ----------------------------------------------------
# Argument construction is tested without a daemon; a real container run
# requires Docker and is covered by the integration job in CI.


def test_non_ascii_output_survives():
    """Regression: on Windows a piped child defaults to the ANSI code page,
    so print("Hello, ...") died with UnicodeEncodeError before the IDE saw a
    byte. Output is decoded as UTF-8, so children are asked to produce it."""
    result = nishachar.run("print('héllo ✓ 日本 🚀')", "python")
    assert result.exit_code == 0, result.stderr
    assert result.stdout.strip() == "héllo ✓ 日本 🚀"


def test_non_ascii_stdin_survives():
    result = nishachar.run("print(input())", "python", stdin="café ✓\n")
    assert result.stdout.strip() == "café ✓"


def test_child_env_does_not_override_an_explicit_choice(monkeypatch):
    from nishachar.runners.local import child_env

    monkeypatch.setenv("PYTHONIOENCODING", "latin-1")
    assert child_env()["PYTHONIOENCODING"] == "latin-1"
    assert child_env()["PYTHONUTF8"] == "1"


def test_child_env_inherits_the_host_path():
    """This tier has no isolation; stripping PATH would only break toolchains."""
    from nishachar.runners.local import child_env

    assert "PATH" in child_env() or "Path" in child_env()


def test_docker_command_applies_every_sandbox_flag():
    argv = DockerRunner().container_argv("python:3.12-slim", Path("/tmp/w"), ["python", "main.py"])
    joined = " ".join(argv)
    assert "--network none" in joined, "containers must not have network access"
    assert "--read-only" in joined
    assert "--cap-drop ALL" in joined
    assert "--security-opt no-new-privileges" in joined
    assert "--memory 256m" in joined
    assert "--pids-limit 128" in joined
    assert "PYTHONUTF8=1" in joined, "containers default to a C locale"
    assert argv[-2:] == ["python", "main.py"]
    assert "--rm" in argv


def test_docker_derives_a_cached_image_only_when_setup_is_needed():
    runner = DockerRunner()
    plain = registry.require("python")
    assert runner.image_for(plain) == plain.image

    she = registry.require("she")
    derived = runner.image_for(she)
    assert derived.startswith("nishachar/she:")
    # Deterministic, so repeated runs reuse the cached image.
    assert derived == runner.image_for(she)


def test_docker_refuses_a_language_with_no_image():
    language = Language(id="noimg", name="NoImage", extensions=(".n",), run=("x",))
    with pytest.raises(ExecutionError, match="no container image"):
        DockerRunner().run("x", language)


# -- runner selection -----------------------------------------------------


def test_get_runner_rejects_an_unknown_name():
    with pytest.raises(ExecutionError, match="unknown runner"):
        get_runner("magic")


def test_auto_runner_prefers_the_local_toolchain():
    auto = get_runner("auto")
    assert auto.pick(registry.require("python")) is auto.local


def test_workspace_is_made_readable_by_the_container(tmp_path: Path):
    """Dropping every capability also drops root's permission bypass.

    Regression test for containers failing with "Permission denied" before the
    program ran, because tempfile's 0700 directory was unreadable to the
    container's uid without CAP_DAC_OVERRIDE.
    """
    from nishachar.runners.docker import _share_with_container

    source = tmp_path / "main.py"
    source.write_text("x", encoding="utf-8")
    tmp_path.chmod(0o700)
    source.chmod(0o600)

    _share_with_container(tmp_path, source)

    if sys.platform != "win32":
        assert tmp_path.stat().st_mode & 0o007 == 0o007, "container needs r-x-w on the workspace"
        assert source.stat().st_mode & 0o004, "container needs to read the source"
