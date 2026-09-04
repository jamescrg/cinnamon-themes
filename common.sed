# Shared colour substitutions, applied to every stylesheet, rc file, SVG and
# XML in every generated theme, before the per-theme <name>.sed.
#
# Darkens Mint-Y's light grey surfaces by 16 points (0x10) so they sit
# between the white content areas and the darker panel. Pure white
# (#ffffff, base_color) and the borders (#c8c8ce, #dbdbdb...) are left alone.
#
# Order matters: a rule whose target is another rule's source must come first
# (#eeeeee is both a stock colour and the target of #fefefe).
s/#eeeeee/#dedede/gI
s/#eeeeef/#dededf/gI
s/#ebebed/#dbdbdd/gI
s/rgba(235, 235, 237,/rgba(219, 219, 221,/g
s/#f0f0f2/#e0e0e2/gI
s/#f2f2f2/#e2e2e2/gI
s/#f3f3f4/#e3e3e4/gI
s/#f6f6f7/#e6e6e7/gI
s/#f8f8f9/#e8e8e9/gI
s/rgba(248, 248, 249,/rgba(232, 232, 233,/g
s/#fbfbfb/#ebebeb/gI
s/#fcfcfc/#ececec/gI
s/#fcfcfd/#ececed/gI
s/#fdfdff/#ededef/gI
s/#fefefe/#eeeeee/gI
s/rgba(254, 254, 254,/rgba(238, 238, 238,/g
# libadwaita window/dialog/sidebar greys, same 16-point shift
s/#fafafb/#eaeaeb/gI
s/#fafafa/#eaeaea/gI
s/#f3f3f5/#e3e3e5/gI
s/#f3f3f3/#e3e3e3/gI

# White content surfaces (text views, lists, entries, cards, popovers) move to
# halfway between Tailwind stone-100 and stone-200 (#eeedec). Only background uses are touched: white as a
# text/icon colour on accents, and translucent white overlays, stay white.
s/background-color: #ffffff/background-color: #eeedec/gI
s/\(@define-color \(theme_base_color\|base_color\|insensitive_base_color\|theme_unfocused_base_color\|content_view_bg\|view_bg_color\|card_bg_color\|popover_bg_color\)\) #ffffff/\1 #eeedec/I
s/\(base_color:\)#ffffff/\1#eeedec/gI
