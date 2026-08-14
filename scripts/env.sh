#!/bin/sh
# Put the workspace-local Rust toolchain on PATH for tauri dev/build.
# Usage: . ./scripts/env.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export RUSTUP_HOME="$ROOT/.rustup"
export CARGO_HOME="$ROOT/.cargo"
export PATH="$CARGO_HOME/bin:$PATH"
