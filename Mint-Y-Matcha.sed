# Mint-Y-Matcha: replace the Mint-Y green accent with Tailwind's lime series,
# anchored at lime-700 (#4d7c0f) as the primary accent.
#   base    #35a854 -> lime-700 #4d7c0f
#   hover   #2f954a -> lime-800 #3f6212
#   pressed #298141 -> lime-900 #365314
#   darkest #10341a -> lime-950 #1a2e05
s/#35a854/#4d7c0f/gI
s/rgba(53, 168, 84,/rgba(77, 124, 15,/g
s/#2f954a/#3f6212/gI
s/rgba(50, 160, 80,/rgba(63, 98, 18,/g
s/#298141/#365314/gI
s/#10341a/#1a2e05/gI
