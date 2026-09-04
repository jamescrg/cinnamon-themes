# Mint-Y-Matcha: replace the Mint-Y green accent with Tailwind's lime series,
# anchored at lime-700 (#4d7c0f) as the primary accent. Applied to every
# stylesheet and SVG in the theme (Cinnamon, GTK 2/3/4, libadwaita, xfwm4,
# openbox); PNG assets are handled by Mint-Y-Matcha.recolor.
#
# Stock shade                 factor  ->  Matcha
#   #35a854 base               1.00       lime-700 #4d7c0f
#   #2f954a/#30974c/#30984c    0.89       #456e0d (lime-700 x 0.89, hover)
#   #298141                    0.77       lime-800 #3f6212 (pressed)
#   #236e37                    0.66       lime-900 #365314
#   #1d5a2d                    0.54       #2a4308 (lime-700 x 0.54)
#   #10341a                    0.31       lime-950 #1a2e05
# Lighter tints are mapped onto the series by relative lightness:
#   #3bbb5e/#3ab85c -> lime-600, #5acb78 -> lime-500, #71d28b/#86cb98 -> lime-400,
#   #9ad4aa/#a4d8b2/#aedcbb -> lime-300, #c2e5cc -> lime-200,
#   #d7eedd/#e1f2e5 -> lime-100, #ebf6ee -> lime-50

# base
s/#35a854/#4d7c0f/gI
s/rgba(53, 168, 84,/rgba(77, 124, 15,/g
# hover
s/#2f954a/#456e0d/gI
s/#30974c/#456e0d/gI
s/#30984c/#456e0d/gI
s/rgba(50, 160, 80,/rgba(73, 118, 14,/g
# pressed and darker
s/#298141/#3f6212/gI
s/rgba(41, 129, 65,/rgba(63, 98, 18,/g
s/#236e37/#365314/gI
s/#1d5a2d/#2a4308/gI
s/rgba(30, 95, 47,/rgba(44, 71, 9,/g
s/#10341a/#1a2e05/gI
# lighter tints
s/#3bbb5e/#65a30d/gI
s/#3ab85c/#65a30d/gI
s/#5acb78/#84cc16/gI
s/#71d28b/#a3e635/gI
s/#86cb98/#a3e635/gI
s/rgba(141, 206, 158,/rgba(163, 230, 53,/g
s/#9ad4aa/#bef264/gI
s/#a4d8b2/#bef264/gI
s/#aedcbb/#bef264/gI
s/#c2e5cc/#d9f99d/gI
s/#d7eedd/#ecfccb/gI
s/#e1f2e5/#ecfccb/gI
s/#ebf6ee/#f7fee7/gI
