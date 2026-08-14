#!/bin/sh
# Stage a self-contained backend (node + @deepseek-ai/dsh) into resources/backend
# so the packaged app does not require `dsh` or `node` on the user's machine.
#
# Fast path: if a complete dsh install already exists on this machine (an npx
# cache, or any path given via DSH_NODE_MODULES), its node_modules is copied
# locally — no network. Otherwise it falls back to `npm install`.
#
# Usage:
#   ./scripts/bundle-backend.sh            # auto-detect or npm install
#   DSH_NODE_MODULES=/path/to/node_modules ./scripts/bundle-backend.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/resources/backend"
DSH_VERSION="${DSH_VERSION:-0.1.0-rc.6}"

# Local npm cache/logs to avoid the root-owned ~/.npm cache (EPERM).
export npm_config_cache="$ROOT/.npm-cache"
export npm_config_logs_dir="$ROOT/.npm-logs"

if ! command -v node >/dev/null 2>&1; then
  echo "error: node not found on PATH (needed to stage the backend)." >&2
  exit 1
fi

NODE_BIN="$(node -e 'process.stdout.write(process.execPath)')"

find_existing_node_modules() {
  if [ -n "$DSH_NODE_MODULES" ] && [ -f "$DSH_NODE_MODULES/@deepseek-ai/dsh/lib/bin.js" ]; then
    echo "$DSH_NODE_MODULES"
    return 0
  fi
  for d in "$HOME"/.npm/_npx/*/node_modules; do
    if [ -f "$d/@deepseek-ai/dsh/lib/bin.js" ] \
       && [ -f "$d/@deepseek-ai/dsh-web-frontend/dist/index.html" ]; then
      echo "$d"
      return 0
    fi
  done
  return 1
}

echo "==> staging backend into $STAGE"
rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "==> copying node binary: $NODE_BIN"
cp "$NODE_BIN" "$STAGE/node"
# Re-sign ad-hoc: macOS arm64 refuses to run binaries without a valid signature,
# and copying can invalidate the original one.
if command -v codesign >/dev/null 2>&1; then
  codesign --force --sign - "$STAGE/node" 2>/dev/null || true
fi

if EXISTING="$(find_existing_node_modules)"; then
  echo "==> reusing existing dsh install: $EXISTING"
  ditto "$EXISTING" "$STAGE/node_modules"
else
  echo "==> no existing dsh install found; installing @deepseek-ai/dsh@$DSH_VERSION"
  cd "$STAGE"
  npm init -y >/dev/null 2>&1
  npm install "@deepseek-ai/dsh@$DSH_VERSION" 2>&1 | tail -8
  cd "$ROOT"
fi

echo "==> verifying staged backend"
"$STAGE/node" "$STAGE/node_modules/@deepseek-ai/dsh/lib/bin.js" --version

echo "==> staged backend size:"
du -sh "$STAGE"
echo "done."
