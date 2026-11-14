# Custom Mint-Y themes

Each `~/.themes/<Ancestor>-Custom` is generated: a fresh copy of
`/usr/share/themes/<Ancestor>` with `cinnamon.patch` applied to
`cinnamon/cinnamon.css` and `Name=` adjusted in `index.theme`.
Do not edit the generated themes by hand; edit `cinnamon.patch` and run
`./rebuild.sh --force`.

* `themes.conf` – which stock themes to derive from, one
  `<ancestor> [<name>|-] [<steps>]` per line; the name defaults to
  `<ancestor>-Custom`, the steps to `panel,spacing,surfaces`
* `steps/` – the shared changes, each a `<step>.patch` (applied to the theme
  tree) or `<step>.sed` (applied to every stylesheet and SVG):
  `panel` darkens the Cinnamon panel, `spacing` spaces out the grouped window
  list, `surfaces` shifts the light greys and moves content areas to stone-100.
  Dark themes only take `spacing`; the other two assume light Mint-Y colours.
* `<name>.sed` – optional per-theme colour substitutions applied to every
  stylesheet, rc file and SVG in the theme (Cinnamon, GTK 2/3/4, libadwaita,
  xfwm4, openbox) after the patch. `Mint-Y-Purple-Custom.sed` darkens the
  purple accent; `Mint-Y-Matcha.sed` maps stock Mint-Y's green shades onto
  Tailwind's lime series anchored at lime-700
* `<name>.recolor` – optional `"#from #to"` pairs; `recolor-png.py` (Pillow)
  remaps accent-hued pixels in every PNG asset (checkboxes, radios, switches,
  window buttons, thumbnails) so the image assets match the CSS
  A third word `exact` on a line selects exact mode, for accents too grey for
  hue matching: pixels that are a blend of the source with any neutral grey
  become the same blend of the target, and a neutral source retints neutral
  pixels of its lightness
* `recolor-png.py` – the PNG recolouring tool; needs `python3-pil`
* `paper-palette.py` – generates `Mint-Y-Paper.sed` and `Mint-Y-Paper.recolor`
  from the built `Mint-Y-Grey-Custom` tree: the palette of jamescraig.dev
  (paper #f2f0ea, ink #3c3836, faded-aqua accent #427b58, tan borders). Every
  grey keeps its lightness and takes the paper's warmth; Mint-Y-Grey's grey
  accent ramp (which mirrors stock Mint-Y's green ramp shade for shade) becomes
  the aqua ramp. `--strength` sets how tan the greys get (0.6 by default, 1.0 is
  gruvbox's own chroma), `--chrome-strength` the same for title bars, header
  bars, sidebars and the Cinnamon menu (0.45), `--panel-strength` for the
  Cinnamon panel alone (0.3), and `--base` the content surfaces (text views, lists, Nemo's file
  area; the blog's subtle shade #edebe5 by default, #f2f0ea is its paper).
  Regenerate after changing `surfaces.sed`, a dial or the stock theme, then
  `./rebuild.sh`:

      ./paper-palette.py ../Mint-Y-Grey-Custom --sed Mint-Y-Paper.sed --recolor Mint-Y-Paper.recolor

* `terminal/` – the matching GNOME Terminal colours (`mint-y-paper.dconf`,
  gruvbox light on the theme's surfaces) and `install-gnome-terminal.sh`, which
  creates or refreshes a "Mint-Y-Paper" profile cloned from your default one
  without changing the default

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
