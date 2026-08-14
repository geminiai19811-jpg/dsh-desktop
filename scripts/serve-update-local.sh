#!/bin/sh
# Serve a locally-signed "new version" so you can test the in-app updater
# without GitHub. Generates a fake newer version (default 9.9.9) in latest.json
# using the REAL signature of the locally built updater bundle, then serves both
# files over a local HTTP server.
#
# Usage:
#   1. Build the signed updater bundle once:
#        . ./scripts/env.sh
#        TAURI_SIGNING_PRIVATE_KEY="$(cat keys/dsh-desktop.key)" \
#        TAURI_SIGNING_PRIVATE_KEY_PASSWORD="" \
#        npx tauri build --bundles app
#   2. Run:  ./scripts/serve-update-local.sh
#   3. Temporarily point tauri.conf.json at the local endpoint (see output),
#      then run the app and use the menu bar → "Check for Updates…".
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8090}"
VERSION="${TEST_VERSION:-9.9.9}"
MACOS="$ROOT/src-tauri/target/release/bundle/macos"
TARBALL="$MACOS/DeepSeek Harness.app.tar.gz"
SIG="$TARBALL.sig"
STAGE="$ROOT/test-update"

if [ ! -f "$TARBALL" ] || [ ! -f "$SIG" ]; then
  echo "error: missing updater artifacts. Build them first (see usage above)." >&2
  exit 1
fi

mkdir -p "$STAGE"
cp "$TARBALL" "$STAGE/app.tar.gz"

python3 - "$SIG" "$VERSION" "$PORT" <<'PY'
import sys, json
sig = open(sys.argv[1]).read().strip()
version, port = sys.argv[2], sys.argv[3]
latest = {
    "version": version,
    "notes": f"Local test update {version}",
    "pub_date": "2026-08-14T00:00:00Z",
    "platforms": {
        "darwin-aarch64": {
            "url": f"http://127.0.0.1:{port}/app.tar.gz",
            "signature": sig,
        }
    },
}
with open("test-update/latest.json", "w") as fh:
    json.dump(latest, fh, indent=2)
print(json.dumps(latest, indent=2))
PY

echo
echo "Serving on: http://127.0.0.1:$PORT/"
echo
echo "Temporarily set tauri.conf.json → plugins.updater to:"
echo "  \"endpoints\": [\"http://127.0.0.1:$PORT/latest.json\"],"
echo "  \"dangerousInsecureTransportProtocol\": true"
echo "(revert with: git checkout src-tauri/tauri.conf.json)"
echo
cd "$STAGE"
python3 -m http.server "$PORT"
