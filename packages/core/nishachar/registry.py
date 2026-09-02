"""The language registry.

A language is data, not code. Every supported language is one JSON file in
``languages/``; adding a language never requires touching this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Language", "Registry", "registry"]


@dataclass(frozen=True)
class Language:
    """One entry from the registry. Mirrors ``languages/schema.json``."""

    id: str
    name: str
    extensions: tuple[str, ...]
    run: tuple[str, ...]
    template: str = ""
    aliases: tuple[str, ...] = ()
    comment: str = "#"
    highlight: str = "text"
    image: str = ""
    setup: tuple[tuple[str, ...], ...] = ()
    compile: tuple[tuple[str, ...], ...] = ()
    browser: str = ""
    website: str = ""
    filename: str = ""

    @property
    def runs_in_browser(self) -> bool:
        return bool(self.browser)

    @property
    def is_compiled(self) -> bool:
        return bool(self.compile)

    def resolve(self, argv, *, file: Path, workdir: Path, binary: Path) -> list[str]:
        """Substitute path placeholders into an argument vector.

        Substitution is per-element and never goes through a shell, so an
        argument like ``-o{bin}`` works and nothing can be injected via a
        filename.
        """
        subs = {
            "{file}": str(file),
            "{dir}": str(workdir),
            "{bin}": str(binary),
            "{stem}": file.stem,
        }
        out = []
        for arg in argv:
            for key, value in subs.items():
                arg = arg.replace(key, value)
            out.append(arg)
        return out

    def to_dict(self) -> dict:
        """JSON-safe form, as served by ``GET /api/languages``."""
        return {
            "id": self.id,
            "name": self.name,
            "extensions": list(self.extensions),
            "aliases": list(self.aliases),
            "comment": self.comment,
            "highlight": self.highlight,
            "template": self.template,
            "website": self.website,
            "browser": self.browser,
            "compiled": self.is_compiled,
        }


def _language_dir() -> Path:
    """Find ``languages/`` whether installed as a wheel or run from a checkout."""
    packaged = Path(__file__).parent / "languages"
    if packaged.is_dir():
        return packaged
    # Development checkout: packages/core/nishachar/registry.py -> repo root.
    checkout = Path(__file__).resolve().parents[3] / "languages"
    if checkout.is_dir():
        return checkout
    raise FileNotFoundError(
        "Could not locate the language registry. Expected it at "
        f"{packaged} or {checkout}."
    )


def _tuples(value) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(step) for step in value or ())


class Registry:
    """Loads language definitions and resolves them by id, alias or extension."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory else _language_dir()
        self._by_id: dict[str, Language] = {}
        self._index: dict[str, Language] = {}
        self.load()

    def load(self) -> None:
        self._by_id.clear()
        self._index.clear()
        for path in sorted(self.directory.glob("*.json")):
            if path.name == "schema.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            data.pop("$schema", None)
            lang = Language(
                id=data["id"],
                name=data["name"],
                extensions=tuple(data["extensions"]),
                run=tuple(data["run"]),
                template=data.get("template", ""),
                aliases=tuple(data.get("aliases", ())),
                comment=data.get("comment", "#"),
                highlight=data.get("highlight", "text"),
                image=data.get("image", ""),
                setup=_tuples(data.get("setup")),
                compile=_tuples(data.get("compile")),
                browser=data.get("browser", ""),
                website=data.get("website", ""),
                filename=data.get("filename", ""),
            )
            if lang.id != path.stem:
                raise ValueError(f"{path.name}: id {lang.id!r} does not match filename")
            if lang.id in self._by_id:
                raise ValueError(f"duplicate language id {lang.id!r}")
            self._by_id[lang.id] = lang
            self._index[lang.id] = lang
            # Aliases and extensions never override a real id.
            for key in (*lang.aliases, *lang.extensions):
                self._index.setdefault(key.lower(), lang)

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self):
        return iter(sorted(self._by_id.values(), key=lambda language: language.name.lower()))

    def get(self, name: str) -> Language | None:
        """Resolve by id, alias, extension (``py`` or ``.py``) or display name."""
        if not name:
            return None
        key = name.strip().lower()
        found = self._index.get(key) or self._index.get(f".{key}")
        if found:
            return found
        return next(
            (lang for lang in self._by_id.values() if lang.name.lower() == key), None
        )

    def require(self, name: str) -> Language:
        found = self.get(name)
        if found is None:
            raise KeyError(
                f"Unknown language {name!r}. Run 'nishachar languages' to list the "
                f"{len(self)} available, or add it: https://github.com/ni-sh-a-char/"
                "ni_sh_a.char-IDE/blob/main/CONTRIBUTING.md"
            )
        return found

    def for_file(self, path: Path | str) -> Language | None:
        """Resolve the language of a file from its extension."""
        path = Path(path)
        # Longest suffix first so '.deno.ts' wins over '.ts'.
        parts = path.name.lower().split(".")
        for start in range(1, len(parts)):
            found = self._index.get("." + ".".join(parts[start:]))
            if found:
                return found
        return None


registry = Registry()
