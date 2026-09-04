#!/bin/bash
# First-time setup on a machine. Run this after cloning the repo to
# ~/.themes/.custom-themes:
#   git clone <remote> ~/.themes/.custom-themes && ~/.themes/.custom-themes/install.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$HERE" in
  "$HOME/.themes/"*) ;;
  *) echo "warning: expected to live under ~/.themes (themes are written to the parent directory: $(dirname "$HERE"))" >&2 ;;
esac

missing=0
for cmd in rsync patch sha256sum systemctl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "missing required command: $cmd" >&2; missing=1; }
done
[ "$missing" = 0 ] || exit 1
[ -d /usr/share/themes ] || { echo "/usr/share/themes not found; is mint-themes installed?" >&2; exit 1; }

"$HERE/rebuild.sh" --force
"$HERE/rebuild.sh" --install-units

echo
echo "Custom themes built. Select one under System Settings > Themes > Desktop, or run e.g.:"
echo "  gsettings set org.cinnamon.theme name 'Mint-Y-Purple-Custom'"
echo "After a 'git pull' on this machine, run: $HERE/rebuild.sh"
