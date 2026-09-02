# The IDE server, containerised.
#
# This image runs ni_sh_a.char-IDE itself. It does not contain 62 toolchains --
# the Docker runner starts a separate, locked-down container per language, so
# mount the host Docker socket if you want the sandboxed tier:
#
#   docker run --rm -p 8777:8777 \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     ghcr.io/ni-sh-a-char/nishachar-ide:2.0.0 --runner docker --host 0.0.0.0
#
# Without the socket it still serves the API and the IDE, using whatever
# toolchains exist in this image (Python, and SHE).

FROM node:22-alpine AS web
WORKDIR /build
COPY packages/web/package.json packages/web/package-lock.json* ./packages/web/
RUN cd packages/web && npm ci --no-audit --no-fund
COPY languages ./languages
COPY packages/web ./packages/web
RUN cd packages/web && npm run build

FROM python:3.12-slim
LABEL org.opencontainers.image.title="ni_sh_a.char-IDE" \
      org.opencontainers.image.description="Run any language, anywhere." \
      org.opencontainers.image.source="https://github.com/ni-sh-a-char/ni_sh_a.char-IDE" \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY packages/core ./packages/core
COPY languages ./languages
COPY --from=web /build/packages/core/nishachar/static ./packages/core/nishachar/static

RUN pip install --no-cache-dir . she-lang \
 && adduser --disabled-password --gecos "" --uid 10001 ide
USER ide

EXPOSE 8777
ENTRYPOINT ["nishachar", "serve", "--host", "0.0.0.0", "--port", "8777"]
