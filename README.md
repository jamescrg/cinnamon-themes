# Custom Mint-Y themes

Each `~/.themes/<Ancestor>-Custom` is generated: a fresh copy of
`/usr/share/themes/<Ancestor>` with `cinnamon.patch` applied to
`cinnamon/cinnamon.css` and `Name=` adjusted in `index.theme`.
Do not edit the generated themes by hand; edit `cinnamon.patch` and run
`./rebuild.sh --force`.

* `themes.conf` – which stock themes to derive from, one `<ancestor> [<name>]`
  per line; the name defaults to `<ancestor>-Custom`
* `cinnamon.patch` – darker panel (#c3c3c6) and grouped-window-list spacing
* `common.sed` – colour substitutions applied to every theme (darkens the
  light grey surfaces by 16 points), run before the per-theme file
* `<name>.sed` – optional per-theme colour substitutions applied to every
  stylesheet, rc file and SVG in the theme (Cinnamon, GTK 2/3/4, libadwaita,
  xfwm4, openbox) after the patch. `Mint-Y-Purple-Custom.sed` darkens the
  purple accent; `Mint-Y-Matcha.sed` maps stock Mint-Y's green shades onto
  Tailwind's lime series anchored at lime-700
* `<name>.recolor` – optional `"#from #to"` pairs; `recolor-png.py` (Pillow)
  remaps accent-hued pixels in every PNG asset (checkboxes, radios, switches,
  window buttons, thumbnails) so the image assets match the CSS
* `recolor-png.py` – the PNG recolouring tool; needs `python3-pil`

Generated themes are complete: select the same name under both Desktop and
Applications in System Settings > Themes.

After a rebuild of the GTK theme you are using, running applications and
Muffin's window title bars keep the old stylesheet until they restart (GTK 3
caches a theme by name for the life of a process). The script sends a
notification when this applies; press Ctrl+Alt+Esc to restart Cinnamon, or run
`./rebuild.sh --restart-cinnamon` to have the script do it.
* `rebuild.sh` – see `./rebuild.sh --help`
* `previous/` – the previous build of each theme, kept until the next rebuild
* `rebuild.log` – what happened and when

The systemd user units `custom-themes.path` / `custom-themes.service`
rebuild automatically when `mint-themes` is upgraded, and at every login.
If the stock CSS changes so that the patch no longer applies, the old theme
is left in place and a critical desktop notification tells you to update the
patch.

To add another light Mint-Y variant, append its name to `themes.conf`, then
run `./rebuild.sh` and `./rebuild.sh --install-units`.

## Using on another machine

This directory is a git repo. Only the inputs are tracked (patch, sed files,
config, scripts); the generated themes, state and logs are ignored and
regenerated per machine.

    git clone <remote> ~/.themes/.custom-themes
    ~/.themes/.custom-themes/install.sh

After pulling changes on a machine, run `./rebuild.sh` (the login-time
service will also pick them up at the next login, because the hashes of the
patch and sed files are part of the up-to-date check).
