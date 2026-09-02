# Built assets

This directory is populated at deploy time by
[`.github/workflows/pages.yml`](../../.github/workflows/pages.yml), which checks
out the `v2.0.0` branch, builds the web component, and copies the bundle here.

Nothing in here is committed, so the site can never ship a stale build and the
demo does not depend on npm having published yet.

To preview the site locally:

```bash
git clone https://github.com/ni-sh-a-char/ni_sh_a.char-IDE.git
cd ni_sh_a.char-IDE

git worktree add .source develop
cd .source/packages/web && npm install && npm run build && cd ../../..
cp .source/packages/web/dist/nishachar-ide.js site/assets/

python -m http.server 8080 --directory site
```

Then open <http://localhost:8080>. The page uses ES modules, so it must be
served over HTTP — opening `index.html` from the filesystem will not work.
