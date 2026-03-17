#!/usr/bin/env bash
# Build and run the K7 multiplayer server (WebSocket + LLM proxy).
# Usage: ./scripts/run-server.sh [--release]
#   --release  build and run in release mode (default: dev)

set -e
cd "$(dirname "$0")/.."

RELEASE=""
for arg in "$@"; do
  case "$arg" in
    --release|-r) RELEASE="--release" ;;
    -h|--help)
      echo "Usage: $0 [--release]"
      echo "  Build and run k7-multiplayer-server. --release for release mode."
      exit 0
      ;;
  esac
done

echo "Building k7-multiplayer-server ${RELEASE:+ (release)}..."
cargo build -p k7-multiplayer-server $RELEASE
echo "Running..."
exec cargo run -p k7-multiplayer-server $RELEASE
