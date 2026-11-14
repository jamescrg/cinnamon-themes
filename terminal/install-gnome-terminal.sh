#!/bin/bash
# Create (or refresh) the "Mint-Y-Paper" GNOME Terminal profile from
# mint-y-paper.dconf. Non-colour settings (font, scrollback, bell...) are
# cloned from the current default profile the first time; the default
# profile itself is not changed. Select the new profile in Terminal >
# Preferences, or make it the default with:
#   gsettings set org.gnome.Terminal.ProfilesList default "$(./install-gnome-terminal.sh --uuid)"
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME=Mint-Y-Paper
BASE=/org/gnome/terminal/legacy/profiles:
list=$(gsettings get org.gnome.Terminal.ProfilesList list)
uuid=""
for p in $(echo "$list" | tr -d "[]',"); do
  if [ "$(gsettings get org.gnome.Terminal.Legacy.Profile:$BASE/:$p/ visible-name)" = "'$NAME'" ]; then uuid=$p; break; fi
done
if [ "${1:-}" = "--uuid" ]; then echo "$uuid"; exit 0; fi
if [ -z "$uuid" ]; then
  uuid=$(uuidgen)
  default=$(gsettings get org.gnome.Terminal.ProfilesList default | tr -d "'")
  # clone everything but the colours from the default profile
  dconf dump "$BASE/:$default/" | grep -vE '^(visible-name|palette|background-color|foreground-color|bold-color|cursor-.*color|highlight-.*color|use-theme-colors|use-theme-background|use-theme-transparency|cursor-colors-set|highlight-colors-set|bold-color-same-as-fg)=' \
    | dconf load "$BASE/:$uuid/"
  gsettings set org.gnome.Terminal.ProfilesList list "$(echo "$list" | sed "s/]$/, '$uuid']/; s/^\[, /[/")"
  echo "created profile $NAME ($uuid)"
else
  echo "updating profile $NAME ($uuid)"
fi
dconf load "$BASE/:$uuid/" < "$HERE/mint-y-paper.dconf"
