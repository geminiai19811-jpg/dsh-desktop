#!/bin/sh
# One-time workspace-local Rust toolchain install (no system-wide changes).
# Installs rustup + a minimal stable toolchain into .rustup/ and .cargo/.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export RUSTUP_HOME="$ROOT/.rustup"
export CARGO_HOME="$ROOT/.cargo"

if [ -x "$CARGO_HOME/bin/cargo" ]; then
  echo "Rust toolchain already present: $("$CARGO_HOME/bin/rustc" --version)"
  exit 0
fi

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
  | sh -s -- -y --profile minimal --default-toolchain stable --no-modify-path

echo
echo "Installed:"
"$CARGO_HOME/bin/rustc" --version
"$CARGO_HOME/bin/cargo" --version
echo
echo "Run '. ./scripts/env.sh' (or rely on the npm scripts) before tauri dev/build."
