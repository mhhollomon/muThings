# Thoughts on positioning.

## Attach
need to :
1. Target any element
2. Target a subsection of that element (if it exists)
    1. Margin
    2. Border
    3. Content - THis always exists.
    4. Full element - This always exist.
3. For piece wise subsections (Margin and Border) need
   to target a piece.
4. Need to say which side of the piece.

cover.border.left.left

## Overlay
Only need the first three since we are going inside.

## Proposal

Lets call ele.sub.piece the _target triple_
- `ele` is the name of an element.
- `sub` is one of `full`, `margin`, `border`, `content`.
- `piece` is one of `left`, `right`, `top`, `bottom`.

`piece` is only allowed if `sub` is one of `margin` or `border`.

`ele` can be quoted, but the others may not.

"Fancy . element".border.left

### Attach
`attach(triple, side, pos_x, pos_y [, anch_x, anch_y] [, offset])`

`side` is one of `left`, `right`, `top`, `bottom`

#### shortcuts
- border.`piece` means cover.border.`piece`
- ele            means ele.full

### Overlay
`overlay(triple, pos_x, pos_y [, anch_x, anch_y] [, offset])`
#### shortcuts
- border.`piece` means cover.border.`piece`
- ele            means ele.content

### grammar
```
attach_pos : "attach" "(" triple "," side "," pos_values ["," anchor_values] ["," offset] ")"

pos_values : (MINMAX | PERCENT) "," (MINMAX | PERCENT)
anchor_values : MINMAX "," MINMAX
side : PIECE
offset : INTEGER

// alteration needed because of the higher priority of SUB_ELEMENT.
// If 'border' is given as the ELEMENT_NAME it will be parsed as
// a SUB_ELEMENT.
triple : (ELEMENT_NAME | SUB_ELEMENT) ["." SUB_ELEMENT] ["." PIECE]

SUB_ELEMENT.10 : /full\b|margin\b|border\b|content\b/i
PIECE.10 : /left\b|right\b|top\b|bottom\b/i
MINMAX : /min\b|mid\b|max\b/i
INTEGER : /\d+/
PERCENT : INTEGER "%"
BARE_STRING : /[^\s\t\n"')(\.,]+/
ELEMENT_NAME : ESCAPED_STRING | BARE_STRING
```


output = (style, (__triple__), __side__, (__pos__), (__anchor__), __offset__)

side will be None for `overlay`
