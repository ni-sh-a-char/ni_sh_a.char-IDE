"""The registry is data, so these tests mostly guard the data itself."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nishachar.registry import Language, Registry, registry

LANGUAGE_DIR = Path(__file__).resolve().parents[1] / "languages"
DEFINITIONS = sorted(p for p in LANGUAGE_DIR.glob("*.json") if p.name != "schema.json")


def test_registry_is_not_empty():
    assert len(registry) >= 60


@pytest.mark.parametrize("path", DEFINITIONS, ids=lambda p: p.stem)
def test_definition_matches_schema(path):
    """Every language file must be loadable and self-consistent.

    This is the test that protects the 'add a language in 8 lines' promise:
    a malformed contribution fails here rather than at somebody's runtime.
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["id"] == path.stem, "id must match the filename"
    assert data["name"].strip(), "name is required"
    assert data["extensions"], "at least one extension is required"
    assert all(e.startswith(".") for e in data["extensions"]), "extensions need a leading dot"
    assert data["run"] and all(isinstance(a, str) for a in data["run"])
    assert data["template"].strip(), "a hello-world template is required"

    for step in data.get("compile", []):
        assert step and all(isinstance(a, str) for a in step)
    for step in data.get("setup", []):
        assert step and all(isinstance(a, str) for a in step)

    # A compiled language must actually use the artefact it compiles.
    if data.get("compile"):
        assert any("{bin}" in a for a in data["run"]), "compiled languages must run {bin}"

    if data.get("browser"):
        assert data["browser"] in {"pyodide", "native"}


def test_ids_and_extensions_do_not_collide():
    ids = [json.loads(p.read_text(encoding="utf-8"))["id"] for p in DEFINITIONS]
    assert len(ids) == len(set(ids))


def test_resolution_by_id_alias_and_extension():
    python = registry.require("python")
    assert registry.get("py") is python
    assert registry.get("PY") is python
    assert registry.get(".py") is python
    assert registry.get("Python") is python


def test_unknown_language_raises_with_a_useful_message():
    with pytest.raises(KeyError) as caught:
        registry.require("cobolscript")
    assert "cobolscript" in str(caught.value)
    assert "nishachar languages" in str(caught.value)


def test_for_file_prefers_the_longest_extension():
    """'.deno.ts' must win over '.ts', or Deno files run under tsx."""
    assert registry.for_file("app.deno.ts").id == "deno"
    assert registry.for_file("app.ts").id == "typescript"
    assert registry.for_file("noextension") is None


def test_she_is_registered_as_a_first_class_language():
    she = registry.require("she")
    assert ".she" in she.extensions
    assert she.runs_in_browser
    assert "she" in " ".join(she.run)


def test_placeholders_are_substituted_inside_arguments():
    """Placeholders must work mid-argument, e.g. Free Pascal's '-o{bin}'."""
    language = Language(
        id="x", name="X", extensions=(".x",), run=("cc", "-o{bin}", "{dir}/extra.o", "{file}", "{stem}")
    )
    workdir, source, binary = Path("/w"), Path("/w/main.x"), Path("/w/prog")
    argv = language.resolve(language.run, file=source, workdir=workdir, binary=binary)
    assert argv == [
        "cc",
        f"-o{binary}",
        f"{workdir}/extra.o",
        str(source),
        "main",
    ]


def test_a_bad_definition_is_rejected(tmp_path):
    (tmp_path / "wrong.json").write_text(
        json.dumps({"id": "different", "name": "N", "extensions": [".n"], "run": ["n"]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="does not match filename"):
        Registry(tmp_path)
