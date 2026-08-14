#!/bin/sh
# Optional: route cargo/npm through the local VPN proxy.
# Usage: . ./scripts/proxy.sh
export http_proxy=http://127.0.0.1:7891
export https_proxy=http://127.0.0.1:7891
export all_proxy=socks5://127.0.0.1:7892
export CARGO_HTTP_PROXY=http://127.0.0.1:7891
export CARGO_HTTPS_PROXY=http://127.0.0.1:7891
