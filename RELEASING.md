# Releasing

The `Release` workflow runs on any `v*` tag. It builds and verifies everything,
then publishes to each registry **only if that registry's credentials are
configured** — so a fork never fails loudly on secrets it was never given.

## One-time setup

Two registries need a human to authorise them once. Until then, those steps
skip or fail while everything else still publishes.

### PyPI — Trusted Publishing (no token to store)

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Add a **pending publisher**:

   | Field | Value |
   |:--|:--|
   | PyPI project name | `nishachar-ide` |
   | Owner | `ni-sh-a-char` |
   | Repository name | `ni_sh_a.char-IDE` |
   | Workflow name | `release.yml` |
   | Environment name | `release` |

3. In the repo, create an environment called `release`
   (Settings → Environments → New environment).

This uses OIDC, so there is no API token to create, rotate, or leak.

### npm

1. Create a **Granular Access Token** with publish rights on the `@nishachar`
   scope at <https://www.npmjs.com/settings/~/tokens>.
2. Add it as the repository secret `NPM_TOKEN`.

The npm job skips cleanly when `NPM_TOKEN` is absent, so nothing breaks in the
meantime.

### GHCR

Nothing to do. It authenticates with the built-in `GITHUB_TOKEN`.

## Cutting a release

```bash
git checkout develop

# 1. Bump the version in both places -- they must match.
#    pyproject.toml            [project] version
#    packages/web/package.json version

# 2. Write the release notes.
$EDITOR CHANGELOG.md

# 3. Verify locally.
python -m pytest && python -m ruff check .
cd packages/web && npm run build && cd ../..

git commit -am "chore: release vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z — <headline>"
git push origin develop --tags
```

Then create the GitHub Release from the tag. The workflow does the rest.

## Version numbers

The Python package, the npm package and the git tag share one version. They
are three faces of one product, and separate numbering would only make bug
reports harder to read.

Semantic versioning applies to the **public surfaces**: the CLI flags, the
`<nishachar-ide>` attributes and events, the HTTP API, the Python API, and the
registry schema. Adding a language is never a breaking change.
