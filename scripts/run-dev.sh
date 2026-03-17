#!/usr/bin/env bash
# Run the Python HTTP server (web assets) and the multiplayer server together.
# Usage: ./scripts/run-dev.sh [--release]
#   HTTP server: http://localhost:8080 (editor at /editor.html)
#   WebSocket server: ws://localhost:8081
#   --release  build/run multiplayer server in release mode

set -e
cd "$(dirname "$0")/.."

RELEASE=""
for arg in "$@"; do
  case "$arg" in
    --release|-r) RELEASE="--release" ;;
    -h|--help)
      echo "Usage: $0 [--release]"
      echo "  Start Python HTTP server (port 8080) and multiplayer server (port 8081)."
      echo "  Open http://localhost:8080/editor.html"
      exit 0
      ;;
  esac
done

HTTP_PID=""
cleanup() {
  if [ -n "$HTTP_PID" ]; then
    kill "$HTTP_PID" 2>/dev/null || true
    wait "$HTTP_PID" 2>/dev/null || true
  fi
  exit 0
}
trap cleanup EXIT INT TERM

echo "Building k7-web WASM (wasm-pack) ..."
(cd crates/k7-web && wasm-pack build --target web --out-dir pkg)

echo "Starting HTTP server (crates/k7-web) on http://localhost:8080 ..."
(
  cd crates/k7-web && exec python3 -m http.server 8080
) &
HTTP_PID=$!
sleep 1

echo "Building and running multiplayer server on ws://localhost:8081 ${RELEASE:+ (release)}..."
cargo build -p k7-multiplayer-server $RELEASE
cargo run -p k7-multiplayer-server $RELEASE
