#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/warden"
UNIT_DIR="$HOME/.config/systemd/user"

rm -rf "$DEST"
mkdir -p "$DEST" "$UNIT_DIR"

cp -r "$SRC_DIR/warden/." "$DEST/"
find "$DEST" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install -m 644 "$SRC_DIR/warden.service" "$UNIT_DIR/warden.service"

systemctl --user daemon-reload
systemctl --user enable --now warden.service

systemctl --user --no-pager status warden.service || true