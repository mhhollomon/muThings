
from typing import Tuple

import re
from lark import Token, Transformer, v_args, visitors

#---------------------------------------------------------
# POSITION
#---------------------------------------------------------
POS_MAP = {
    'bottom' : 'max',
    'center' : 'mid',
    'top' : 'min',
    'right' : 'max',
    'left' : 'min'
}
# reference(width, height, [offset], [side]) -- side only for border.
POS_PATTERN = re.compile(r'(\w+) \( \s* (\w+) \s*,\s* (\w+) (?: \s*,\s* (\d+))? (?: \s*,\s* (\w+))? \s* \)', re.RegexFlag.X)

# pixel (width, height, [w anchor], [h anchor])
PIXEL_PATTERN = re.compile(r'pixel \s* \( \s* (\d+\%?) \s*,\s* (\d+\%?)  (?: \s*,\s* (\w+))? (?: \s*,\s* (\w+))? \s* \)', re.RegexFlag.X)

# attach (ref, side, [offset], [anchor])
ATTACH_PATTERN = re.compile(r'attach \s* \( \s* (\w+) \s*,\s* (\w+) (?: \s*,\s* (\d+))? (?: \s*,\s* (\w+))? \s* \)', re.RegexFlag.X)

# ('style', ('ele', 'sub', 'side'), (x, y), (anc_x, anc_y), offset)
# center-center-10 =>
# ('overlay', ('output', 'content', None), ( 50%, 50%), ('mid', 'mid'), 10)
# overlay(border:left, min, mid, 10) =>
# ('overlay', ('cover', 'border', 'left'), ( 0%, 50%), ('min', 'mid'), 10)
# attach("something fancy", 20%, mid, mid, mid, 15) =>
# ('attach', ('something fancy', content, None), ( 20%, 50%), ('mid', 'mid'), 15)

class position :
    def __init__(self, pos_str : str ) -> None :
        self.pos_str = pos_str
        self.ptype = ''

        # valid() method to query
        self._valid = False

        # relative (min, mid, max) used by simple
        # use w and h porperties to query
        self._width = ''
        self._height = ''

        # offset for the position (int) used by attach and function
        self.offset = 0

        # reference item - used by attach and function
        self.ref = ''

        # side of the reference item - used by attach and border
        self.side = ''

        # what part of the item to use when calculating position
        self.anchor : Tuple[str, str] = ('min', 'min')

        # used by attach. Which part of the ref element side to use
        # when calculating position. Defaults to mid
        self.ref_anchor : str = 'mid'

        if self.pos_str is None :
            return 
        
        self.pos_str = self.pos_str.strip().lower()

        if self.pos_str == '' :
            return

        if '-' in self.pos_str :
            self._parse_simple()
        elif '(' in self.pos_str :
            self._parse_function()
        else :
            raise ValueError(f"Invalid position string: {pos_str}")

    def __str__(self) -> str :
        return f'"{self.pos_str}"'

    def _parse_simple(self) :
            p = self.pos_str.split('-')
            if len(p) < 2 or len(p) > 3 :
                raise ValueError(f"Invalid simple position string: {self.pos_str}")
            w = p[0].strip()
            h = p[1].strip()
            offset = int(p[2].strip()) if len(p) == 3 else 10
            if w not in ('left', 'center', 'right') :
                raise ValueError(f"Invalid width in position string: {self.pos_str}")
            
            if h not in ('top', 'center', 'bottom') :
                raise ValueError(f"Invalid height in position string: {self.pos_str}")
        
            self._width = POS_MAP[w]
            self._height = POS_MAP[h]
            self.offset = offset
            self.ref = 'output'
            self._valid = True
            self.ptype = 'simple'

    def _parse_attach(self) :
        m = ATTACH_PATTERN.fullmatch(self.pos_str)
        if not m :
            raise ValueError(f"Invalid attach position string: {self.pos_str}")

        self.ref = m.groups()[0]
        self.side = m.groups()[1]
        self.ptype = 'attach'
        self.offset = int(m.groups()[2] or 0)
        self.ref_anchor = m.groups()[3] or 'mid'
        self._valid = True

    def _parse_function(self) :

        if self.pos_str.startswith('pixel') :
            self._parse_pixel()
            return

        if self.pos_str.startswith('attach') :
            self._parse_attach()
            return
        
        m = POS_PATTERN.fullmatch(self.pos_str)
        if not m :
            raise ValueError(f"Invalid function position string: {self.pos_str}")

        ref, width, height, offset, side = m.groups()

        if ref not in ('output', 'cover', 'border', 'full_output') :
            raise ValueError(f"Invalid reference in position string: {self.pos_str}")

        if width not in ('min', 'mid', 'max') :
            raise ValueError(f"Invalid width in position string: {self.pos_str}")

        if height not in ('min', 'mid', 'max') :
            raise ValueError(f"Invalid height in position string: {self.pos_str}")
        
        if ref == 'border' :
            if side not in ('left', 'right', 'top', 'bottom') :
                raise ValueError(f"Invalid side in position string: {self.pos_str}")
        elif side is not None :
                raise ValueError(f"Cannot give side unless reference is border in position string: {self.pos_str}")

        self._width = width
        self._height = height
        self.ref = ref
        self.offset = int(offset or 0)
        self._valid = True
        self.side = side or ''
        self.ptype = 'function'

    def _parse_pixel(self) :
        m = PIXEL_PATTERN.fullmatch(self.pos_str)
        if not m :
            return False

        width, height = m.groups()[0:2]
        if len(m.groups()) == 3 :
            self.anchor = (m.groups()[2], 'mid')
        elif len(m.groups()) == 4 :
            self.anchor = (m.groups()[2] or 'min', m.groups()[3] or 'mid')

        self._width = width
        self._height = height
        self.ref = 'output'

        self._valid = True
        self.ptype = 'pixel'
        return True

    def valid(self) -> bool:
        return self._valid
    
    @property
    def w(self) -> str :
        return self._width

    @property
    def h(self) -> str :
        return self._height
    


class positionXform(Transformer) :

    def __default__(self, data, children, meta) :
        print(f"===== Calling default for {data}")
        return super().__default__(data, children, meta)

    @v_args(inline=True)
    def start(self, s : tuple) -> tuple:
        return s

    @v_args(inline=True)
    def INTEGER(self, s : Token) -> int:
        return int(s.value)

    def WS(self, _) :
        return visitors.Discard

    @v_args(inline=True)
    def STRING_VALUE(self, s : Token) -> str:
        value = s.value
        if value.startswith('"') :
            value = value[1:-1]
        return value

    @v_args(inline=True)
    def PERCENT(self, s : Token) -> int:
        return int(s.value[:-1])

    @v_args(inline=True)
    def REF_STRING_VALUE(self, s : Token) -> str:
        value = s.value
        if value.startswith('"') :
            value = value[1:-1]
        return value

    @v_args(inline=True)
    def POS_VALUE(self, s : Token) -> str | int:
        value = s.value
        if value.endswith('%') :
            value = int(value[:-1])
        return value

    @v_args(inline=True)
    def WORD(self, s : Token) -> str:
        return s.value

    @v_args(inline=True)
    def MINMAX(self, s : Token) -> str:
        return s.value
    
    @v_args(inline=True)
    def simple_pos(self, w, h, offset):
        if offset is None :
            offset = 10

        if w == 'left' :
            w = 0
            anchor_w = 'min'
        elif w == 'center' :
            w = 50
            anchor_w = 'mid'
        elif w == 'right' :
            w = 100
            anchor_w = 'max'
        else :
            raise ValueError(f"Invalid width in position string: {w}")

        if h == 'top' :
            h = 0
            anchor_h = 'min'
        elif h == 'center' :
            h = 50
            anchor_h = 'mid'
        elif h == 'bottom' :
            h = 100
            anchor_h = 'max'
        else :
            raise ValueError(f"Invalid height in position string: {h}")

        return ('overlay', ('output', 'content', None), (w, h), (anchor_w, anchor_h), offset)

    @v_args(inline=True)
    def attach_pos(self, ref, pos, anchor, offset) :
        print(f"ref: {ref}, pos: {pos}, anchor: {anchor}, offset: {offset}")
        if offset is not None :
            offset = int(offset)
        if anchor is None :
            if isinstance(pos[0], int) :
                anchor_x = 'max' if pos[0] > 70 else 'min' if pos[0] < 30 else 'mid'
            else :
                anchor_x = pos[0]

            if isinstance(pos[1], int) :
                anchor_y = 'max' if pos[1] > 70 else 'min' if pos[1] < 30 else 'mid'
            else :
                anchor_y = pos[1]
            anchor = (anchor_x, anchor_y)

        return ('attach', ref, pos, anchor, offset)

    def ref_value(self, children) -> tuple :
        ref_ele = children[0]
        sub_ele = None
        side = None
        if ref_ele == 'border' :
            ref_ele = 'cover'
            sub_ele = 'border'
            if children[2] is not None:
                raise ValueError(f"Invalid reference value: {children}")
            if children[1] in ('left', 'right', 'top', 'bottom') :
                side = children[1]
        elif children[1] in ('left', 'right', 'top', 'bottom') :
            side = children[1]
            sub_ele = 'content'
        elif len(children) != 3 :
            raise ValueError(f"Invalid reference value: {children}")
        else :
            sub_ele = children[1]
            side = children[2]
            if side not in ('left', 'right', 'top', 'bottom') :
                raise ValueError(f"Invalid side in reference value: {children}")


        return (ref_ele, sub_ele, side)

    @v_args(inline=True)
    def one_pos_value(self,  t : Token | str) :
        if isinstance(t, Token) :
            value = t.value
        else :
            value = t
        if isinstance(value, str) :
            if value not in ('min', 'mid', 'max') :
                raise ValueError(f"Invalid position value in position string: {value}")
        elif isinstance(value, int) :
            if value > 100 :
                raise ValueError(f"Invalid position value in position string: {value}%")
        
        return value

    @v_args(inline=True)
    def pos_values(self, left, right) :
        return (left, right)

    @v_args(inline=True)
    def anchor_values(self, x, y) :
        return (x, y)

    @v_args(inline=True)
    def offset(self, x) :
        return x

