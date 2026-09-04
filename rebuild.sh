#!/bin/bash
# Rebuild ~/.themes/<Ancestor>-Custom from /usr/share/themes/<Ancestor> plus
# cinnamon.patch, for every ancestor listed in themes.conf.
#
#   rebuild.sh                 rebuild themes whose ancestor/patch changed
#   rebuild.sh --force         rebuild everything
#   rebuild.sh --check         report what is out of date, change nothing
#   rebuild.sh --settle        wait for /usr/share/themes to stop changing first
#                              (used by the systemd service during apt upgrades)
#   rebuild.sh --install-units (re)generate and enable the systemd user units
#   rebuild.sh --restart-cinnamon
#                              after rebuilding, restart Cinnamon if the active
#                              GTK theme changed (Muffin caches a theme's CSS
#                              until restart, so window title bars go stale)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_DIR="$(dirname "$HERE")"
STOCK=/usr/share/themes
PATCH="$HERE/cinnamon.patch"
CONF="$HERE/themes.conf"
STATE="$HERE/state"
LOG="$HERE/rebuild.log"
SUFFIX="-Custom"
UNIT_DIR="$HOME/.config/systemd/user"

FORCE=0 SETTLE=0 CHECK=0 INSTALL=0 RESTART=0
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    --settle) SETTLE=1 ;;
    --check) CHECK=1 ;;
    --install-units) INSTALL=1 ;;
    --restart-cinnamon) RESTART=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG" >&2; }
notify() { command -v notify-send >/dev/null 2>&1 && notify-send -u "${3:-normal}" -a "Custom themes" "$1" "$2" 2>/dev/null || true; }
# themes.conf lines are "<ancestor> [<output name>]"; the name defaults to <ancestor>-Custom.
entries() { grep -Ev '^[[:space:]]*(#|$)' "$CONF" | tr -d '\r' | awk -v s="$SUFFIX" '{ print $1, ($2 != "" ? $2 : $1 s) }'; }
ancestors() { entries | awk '{ print $1 }'; }
tree_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -d' ' -f1; }
# Hash contents only: "sha256sum FILE" prints the path beside the hash, which
# would make the stamp depend on how this script was invoked (./rebuild.sh vs
# an absolute path), forcing a needless full rebuild every time.
file_hash() { sha256sum < "$1" | cut -d' ' -f1; }
stamp() {
  { tree_hash "$STOCK/$1"; file_hash "$PATCH"; file_hash "$0"; file_hash "$HERE/recolor-png.py"
    for f in "$HERE/common.sed" "$HERE/$2.sed" "$HERE/$2.recolor"; do [ -f "$f" ] && file_hash "$f"; done; true
  } | sha256sum | cut -d' ' -f1
}
all_hash() { for A in $(ancestors); do [ -d "$STOCK/$A" ] && tree_hash "$STOCK/$A"; done | sha256sum; }

install_units() {
  mkdir -p "$UNIT_DIR"
  {
    echo "[Unit]"
    echo "Description=Rebuild custom themes when their stock ancestors change"
    echo
    echo "[Path]"
    echo "PathChanged=$STOCK"
    for A in $(ancestors); do
      echo "PathChanged=$STOCK/$A"
      echo "PathChanged=$STOCK/$A/cinnamon"
    done
    echo "Unit=custom-themes.service"
    echo
    echo "[Install]"
    echo "WantedBy=default.target"
  } > "$UNIT_DIR/custom-themes.path"
  cat > "$UNIT_DIR/custom-themes.service" <<UNIT
[Unit]
Description=Rebuild custom themes from their stock ancestors

[Service]
Type=oneshot
ExecStart=$HERE/rebuild.sh --settle

[Install]
WantedBy=default.target
UNIT
  systemctl --user daemon-reload
  systemctl --user enable --now custom-themes.path >/dev/null 2>&1
  systemctl --user enable custom-themes.service >/dev/null 2>&1
  log "installed systemd user units custom-themes.path and custom-themes.service"
}

if [ "$INSTALL" = 1 ]; then install_units; exit 0; fi

[ -f "$CONF" ] || { log "missing $CONF"; exit 1; }
[ -f "$PATCH" ] || { log "missing $PATCH"; exit 1; }

if [ "$SETTLE" = 1 ]; then
  # An apt upgrade replaces files one by one; wait until nothing changes for 10s.
  h1=$(all_hash)
  for _ in $(seq 1 18); do
    sleep 10
    h2=$(all_hash)
    [ "$h1" = "$h2" ] && break
    h1=$h2
  done
fi

mkdir -p "$STATE" "$HERE/build" "$HERE/previous"
rebuilt=() failed=() stale=0
while read -r A name; do
  src="$STOCK/$A"; dest="$THEMES_DIR/$name"
  if [ ! -d "$src" ]; then
    log "$name: ancestor $src does not exist, skipping"; failed+=("$name"); continue
  fi
  want=$(stamp "$A" "$name"); have=$(cat "$STATE/$name" 2>/dev/null || echo none)
  if [ "$want" = "$have" ] && [ "$FORCE" = 0 ] && [ -d "$dest" ]; then
    [ "$CHECK" = 1 ] && echo "$name: up to date"
    continue
  fi
  if [ "$CHECK" = 1 ]; then echo "$name: rebuild needed"; stale=1; continue; fi

  build="$HERE/build/$name"
  rm -rf "$build"; mkdir -p "$build"
  rsync -a --delete "$src/" "$build/"
  if ! patch -p1 -F0 --dry-run --no-backup-if-mismatch -d "$build" < "$PATCH" >>"$LOG" 2>&1; then
    log "$name: cinnamon.patch no longer applies to $src; existing theme left untouched"
    notify "Custom theme NOT updated" "$name: the stock theme changed and cinnamon.patch needs updating. See $LOG" critical
    failed+=("$name"); rm -rf "$build"; continue
  fi
  patch -p1 -F0 --no-backup-if-mismatch -d "$build" < "$PATCH" >>"$LOG" 2>&1
  # Colour substitutions apply to every stylesheet, rc file, SVG and XML in the
  # theme: common.sed for all themes first, then the per-theme file.
  for sedfile in "$HERE/common.sed" "$HERE/$name.sed"; do
    [ -f "$sedfile" ] || continue
    find "$build" -type f \( -name '*.css' -o -name '*.svg' -o -name '*.xml' -o -name '*.rc' -o -name gtkrc -o -name themerc \) \
      -exec sed -i -f "$sedfile" {} +
    log "$name: applied colour substitutions from $(basename "$sedfile")"
  done
  if [ -f "$HERE/$name.recolor" ]; then
    # PNG assets (checkboxes, switches, thumbnails...) get their accent pixels remapped.
    mapargs=()
    while read -r from to; do
      [[ "$from" =~ ^#[0-9a-fA-F]{6}$ && "$to" =~ ^#[0-9a-fA-F]{6}$ ]] && mapargs+=(-m "$from $to")
    done < <(grep -Ev '^[[:space:]]*(#[^0-9a-fA-F]|#$|$)' "$HERE/$name.recolor")
    if [ ${#mapargs[@]} -gt 0 ]; then
      find "$build" -type f -name '*.png' -print0 | xargs -0 python3 "$HERE/recolor-png.py" "${mapargs[@]}" >>"$LOG" 2>&1
      log "$name: recoloured PNG assets per $name.recolor"
    fi
  fi
  sed -i "s/^Name=.*/Name=$name/; s/^GtkTheme=.*/GtkTheme=$name/" "$build/index.theme"

  prev="$HERE/previous/$name"; rm -rf "$prev"
  [ -e "$dest" ] && mv "$dest" "$prev"
  mv "$build" "$dest"
  echo "$want" > "$STATE/$name"
  log "$name: rebuilt from $src ($(dpkg-query -W -f='mint-themes ${Version}' mint-themes 2>/dev/null || echo 'unknown version'))"
  rebuilt+=("$name")
done < <(entries)

if [ "$CHECK" = 1 ]; then exit "$stale"; fi

if [ ${#rebuilt[@]} -gt 0 ]; then
  # Make a running Cinnamon reload the desktop theme if it is one we just rebuilt.
  current=$(gsettings get org.cinnamon.theme name 2>/dev/null | tr -d "'" || true)
  for n in "${rebuilt[@]}"; do
    if [ "$n" = "$current" ]; then
      gsettings set org.cinnamon.theme name '' && sleep 1 && gsettings set org.cinnamon.theme name "$current" && log "reloaded Cinnamon theme $current"
    fi
  done
  notify "Custom themes updated" "$(printf '%s ' "${rebuilt[@]}")"

  # Muffin draws window title bars from the GTK theme but caches its CSS for
  # the life of the Cinnamon process, so a rebuilt active GTK theme needs a
  # Cinnamon restart before title bars match the applications.
  gtk_current=$(gsettings get org.cinnamon.desktop.interface gtk-theme 2>/dev/null | tr -d "'" || true)
  for n in "${rebuilt[@]}"; do
    if [ "$n" = "$gtk_current" ] && [ -n "${DISPLAY:-}" ]; then
      if [ "$RESTART" = 1 ]; then
        log "restarting Cinnamon so title bars pick up $gtk_current"
        setsid nohup cinnamon --replace >/dev/null 2>&1 < /dev/null &
      else
        notify "Restart Cinnamon to refresh title bars" "Press Ctrl+Alt+Esc (or run rebuild.sh --restart-cinnamon) so window title bars pick up the rebuilt $gtk_current."
      fi
    fi
  done
fi
[ ${#failed[@]} -eq 0 ]
