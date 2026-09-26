#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now warden.service || true
rm -rf "$HOME/.local/warden"
rm -f "$HOME/.config/systemd/user/warden.service"
systemctl --user daemon-reload