#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC="$REPO_ROOT/src/main/resources/python/cadmium"
DEST="$SCRIPT_DIR/package/bundled/cadmium-src/cadmium"

echo "Syncing $SRC -> $DEST"
rsync -a --delete "$SRC/" "$DEST/"

cd "$SCRIPT_DIR/package"
echo "Building extension package"
npm run package
