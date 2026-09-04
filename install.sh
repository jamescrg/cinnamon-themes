#!/bin/bash
# First-time setup on a machine. Run this after cloning the repo to
# ~/.themes/.custom-themes:
#   git clone <remote> ~/.themes/.custom-themes && ~/.themes/.custom-themes/install.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_DIR="$(dirname "$HERE")"

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

# Flatpak apps cannot see ~/.themes: the sandbox exposes only its runtime's
# /usr/share/themes plus any org.gtk.Gtk3theme.<name> extension from flathub,
# and no such extension exists for a locally generated theme. GTK then falls
# back to Adwaita silently, so a flatpak app keeps Adwaita's blue accent while
# every host app follows the custom theme. A read-only bind of the themes
# directory fixes it for all flatpaks. (Host icon themes are already visible
# via /run/host/share/icons, so only themes need this.)
if command -v flatpak >/dev/null 2>&1; then
  case "$THEMES_DIR" in
    "$HOME"/*) fs="~/${THEMES_DIR#"$HOME"/}" ;;
    *) fs="$THEMES_DIR" ;;
  esac
  if flatpak override --user "--filesystem=$fs:ro" 2>/dev/null; then
    echo "flatpak: granted read-only access to $fs for all applications"
    echo "         (running flatpak apps must be restarted to pick up the theme)"
  else
    echo "warning: could not set the flatpak override; flatpak apps will use Adwaita" >&2
  fi
fi

echo
echo "Custom themes built. Select one under System Settings > Themes > Desktop, or run e.g.:"
echo "  gsettings set org.cinnamon.theme name 'Mint-Y-Purple-Custom'"
echo "After a 'git pull' on this machine, run: $HERE/rebuild.sh"
