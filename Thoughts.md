# Thoughts on positioning.

## Attach
need to :
1. Target any element
2. Target a subsection of that element (if it exists)
    a. Margin
    b. Border
    c. Content
    d. Full element
3. For piece wise subsections (Margin and Border) need
   to target a piece
4. Need to say which side of the piece

cover.border.left.left

## Overlay
Only need the first three since we are going inside.

## Proposal

Lets call the ele.sub.piece the _target triple_
`sub` is one of `full`, `margin`, `border`, `content`
`piece` is one of `left`, `right`, `top`, `bottom`
`piece` is only allowed in `sub` is one of `margin` or `border`

`ele` can be quoted, but the others may not.

"Fancy . element".border.left

### Attach
`attach(triple, side, pos_x, pos_y [, anch_x, anch_y] [, offset])`
#### shortcuts
border.`piece` means cover.border.`piece`
ele.`piece`    means ele.border.`piece`
ele            means ele.full

### Overlay
`overlay(triple, pos_x, pos_y [, anch_x, anch_y] [, offset])`
#### shortcuts
border.`piece` means cover.border.`piece`
ele.`piece`    means ele.border.`piece`
ele            means ele.content

### grammar
SUB_ELEMENT : /full|margin|border|content/i
PIECE : /left|right|top|bottom/i
BARE_STRING : /[^\s\t\n"')(\.]+/
ELEMENT_NAME : ESCAPED_STRING | BARE_STRING

triple : ELEMENT_NAME ["." SUB_ELEMENT] ["." PIECE]

