# The website

The landing page and documentation for ni_sh_a.char-IDE, deployed to GitHub
Pages from this directory on every push to `main`.

| File | What it is |
|:--|:--|
| `index.html` | Landing page. The hero is a live, working IDE — not a screenshot. |
| `docs/index.html` | Documentation: CLI, component API, HTTP API, registry format. |
| `assets/` | Populated at deploy time. See [assets/README.md](assets/README.md). |

Both pages are hand-written HTML with inline CSS. There is no site generator,
no build step and no framework: the whole thing is two files and a bundle, which
means it cannot rot and anyone can edit it.

Local preview instructions are in [assets/README.md](assets/README.md).
