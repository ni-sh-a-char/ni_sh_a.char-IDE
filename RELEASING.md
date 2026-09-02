# Releasing

The `Release` workflow runs on any `v*` tag and publishes to five registries.
Each step runs **only if that registry's credentials are configured**, so a
fork never fails loudly on secrets it was never given, and you can enable them
one at a time.

| Registry | Package | Auth | Status |
|:--|:--|:--|:--|
| PyPI | `nishachar-ide` | OIDC + `vars.PUBLISH_PYPI` | needs one-time setup |
| npm | `@nishachar/ide` | `NPM_TOKEN` | needs one-time setup |
| pub.dev | `nishachar_ide` | OIDC + `vars.PUBLISH_PUB` | needs one-time setup |
| Maven Central | `io.github.ni-sh-a-char:nishachar-ide` | token + GPG | needs one-time setup |
| GHCR | `ghcr.io/ni-sh-a-char/nishachar-ide` | built-in | ✅ working |

Each job **skips** when its credentials are absent rather than failing, so a
release is green from the first tag and turns on one registry at a time. The
two OIDC registries have no secret to probe, so they are enabled with a
repository variable (**Settings → Secrets and variables → Actions →
Variables**) once their one-time setup is done:

| Variable | Set to `true` after |
|:--|:--|
| `PUBLISH_PYPI` | the pending publisher exists on pypi.org (step 1) |
| `PUBLISH_PUB` | automated publishing is enabled on pub.dev (step 3) |

---

## One-time setup

Do these once. After that every release is a tag.

### 0. Create the `release` environment

Repo **Settings → Environments → New environment**, named exactly `release`.
Every publish job targets it, which also gives you a place to add a required
reviewer if you ever want releases gated.

### 1. PyPI — Trusted Publishing

No API token to create, store, rotate, or leak.

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Add a **pending publisher**:

   | Field | Value |
   |:--|:--|
   | PyPI project name | `nishachar-ide` |
   | Owner | `ni-sh-a-char` |
   | Repository name | `ni_sh_a.char-IDE` |
   | Workflow name | `release.yml` |
   | Environment name | `release` |

Then set the repository variable `PUBLISH_PYPI` to `true`. The next tagged
release claims the name and publishes.

### 2. npm

1. Create a **Granular Access Token** at
   <https://www.npmjs.com/settings/~/tokens> with **Read and write** on the
   `@nishachar` scope.
2. Repo **Settings → Secrets and variables → Actions → New repository secret**:
   `NPM_TOKEN`.

The scope `@nishachar` is created automatically on first publish.

### 3. pub.dev

pub.dev only offers automated publishing for a package that already exists, so
the **first** publish is manual and must come from your Google account:

```bash
cd packages/dart
dart pub publish          # opens a browser to authenticate
```

Then enable automation for every release after that:

1. <https://pub.dev/packages/nishachar_ide/admin>
2. **Automated publishing → Enable publishing from GitHub Actions**
3. Repository: `ni-sh-a-char/ni_sh_a.char-IDE`, tag pattern: `v{{version}}`
4. Set the repository variable `PUBLISH_PUB` to `true`.

### 4. Maven Central

The most involved, because Central requires every artifact to be GPG-signed.

**a. Claim the namespace** — free, verified through GitHub:

1. Register at <https://central.sonatype.com/> (sign in with GitHub).
2. **Namespaces → Add Namespace** → `io.github.ni-sh-a-char`.
3. Central gives you a generated repository name. Create a public repo with
   exactly that name under the `ni-sh-a-char` org, then click **Verify**. You
   can delete that repo afterwards.

**b. Generate a user token:** Central → your account → **Generate User Token**.
It gives you a username and password pair.

**c. Create a signing key**, if you do not already have one:

```bash
gpg --gen-key                      # use piyushmishra.professional@gmail.com
gpg --list-secret-keys --keyid-format=long     # note the key id

# Publish the public half, or Central will reject the upload:
gpg --keyserver keyserver.ubuntu.com --send-keys <KEY_ID>

# Export the private half for CI:
gpg --armor --export-secret-keys <KEY_ID>
```

**d. Add four repository secrets:**

| Secret | Value |
|:--|:--|
| `MAVEN_CENTRAL_USERNAME` | the token username from step b |
| `MAVEN_CENTRAL_PASSWORD` | the token password from step b |
| `GPG_PRIVATE_KEY` | the entire `--armor --export-secret-keys` block, `-----BEGIN` line included |
| `GPG_PASSPHRASE` | the passphrase for that key |

> Keep the private key and passphrase out of the repository, out of commit
> messages, and out of chat. They are the only credentials here that can sign
> artifacts in your name.

---

## Cutting a release

```bash
git checkout v2.0.0

# 1. Bump the version everywhere. All four must match.
#    pyproject.toml                  [project] version
#    packages/web/package.json       version
#    packages/dart/pubspec.yaml      version
#    packages/kotlin/pom.xml         <version>

# 2. Regenerate the clients if languages/ changed.
python tools/generate_bindings.py

# 3. Write the release notes.
$EDITOR CHANGELOG.md
$EDITOR packages/dart/CHANGELOG.md    # pub.dev shows this on the listing

# 4. Verify locally, exactly as CI will.
python -m pytest && python -m ruff check .
cd packages/web    && npm ci && npm run build   && cd ../..
cd packages/dart   && dart pub get && dart test && dart pub publish --dry-run && cd ../..
cd packages/kotlin && mvn -B verify             && cd ../..

git commit -am "chore: release vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z — <headline>"
git push origin refs/heads/v2.0.0 && git push origin vX.Y.Z
```

Then create the GitHub Release from the tag. The workflow does the rest.

> **Note on ref names.** Branches and tags share the names `v1.0.0` and
> `v2.0.0`, so a bare `v2.0.0` is ambiguous to git. Automation uses fully
> qualified refs (`refs/heads/v2.0.0`, `refs/tags/v2.0.0`); do the same in
> scripts.

## Verifying a release

```bash
pip install --no-cache-dir nishachar-ide==X.Y.Z && nishachar --version
npm view @nishachar/ide version
dart pub cache add nishachar_ide -v X.Y.Z
mvn dependency:get -Dartifact=io.github.ni-sh-a-char:nishachar-ide:X.Y.Z
docker run --rm ghcr.io/ni-sh-a-char/nishachar-ide:X.Y.Z --version
```

Maven Central takes up to 30 minutes to appear in search, and up to 4 hours to
show on the website. The artifact is usable before it is searchable.

## Version numbers

All five artifacts share one version. They are faces of one product, and
separate numbering would only make bug reports harder to read.

Semantic versioning applies to the **public surfaces**: CLI flags, the
`<nishachar-ide>` attributes and events, the HTTP API, the Python, Dart and
Kotlin APIs, and the registry schema. Adding a language is never a breaking
change.
