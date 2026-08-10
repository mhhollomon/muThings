
from typing import Tuple

import re

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

    def _parse_simple(self) :
            w, h = self.pos_str.split('-')
            w = w.strip()
            h = h.strip()
            if w not in ('left', 'center', 'right') :
                raise ValueError(f"Invalid width in position string: {self.pos_str}")
            
            if h not in ('top', 'center', 'bottom') :
                raise ValueError(f"Invalid height in position string: {self.pos_str}")
        
            self._width = POS_MAP[w]
            self._height = POS_MAP[h]
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

        if ref not in ('output', 'cover', 'border') :
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
    
