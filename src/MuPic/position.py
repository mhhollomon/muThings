
from dataclasses import dataclass
import re

import logging
from typing import Tuple
logger = logging.getLogger(__name__)

#---------------------------------------------------------

GEOMETRY_PATTERN = re.compile(r'(\d+)x(\d+)')
@dataclass
class geometry :
    width : int
    height : int

    def to_tuple(self) -> tuple :
        return (self.width, self.height)

    def __getitem__(self, key) :
        return self.to_tuple()[key]
    
    @classmethod
    def from_string(cls, s : str | None) -> 'geometry | None' :
        if s is None :
            return None
        
        match = GEOMETRY_PATTERN.match(s)
        if match is None :
            raise ValueError(f"Invalid geometry string: {s}")

        width, height = match.groups()
        return cls(int(width), int(height))
    
    def is_square(self) -> bool :
        return self.width == self.height
    
    def is_portrait(self) -> bool :
        return self.width < self.height
    
    def is_landscape(self) -> bool :
        # "square" should be treated as landscape
        return self.width >= self.height

#---------------------------------------------------------

@ dataclass
class rectangle :
    start : geometry
    extent: geometry

    def to_tuple(self) -> tuple :
        return (self.start.to_tuple(), self.extent.to_tuple())
    
    def copy(self) -> 'rectangle' :
        return rectangle(geometry(self.start.width, self.start.height), 
                         geometry(self.extent.width, self.extent.height)) 

#---------------------------------------------------------

POS_MAP = {
    'bottom' : 'max',
    'center' : 'mid',
    'top' : 'min',
    'right' : 'max',
    'left' : 'min'
}
# reference(width, height, [side]) -- side only for border.
POS_PATTERN = re.compile(r'(\w+) \( \s* (\w+) \s*,\s* (\w+) (?: \s*,\s* (\w+))? \s* \)', re.RegexFlag.X)

# pixel (width, height, [w anchor], [h anchor])
PIXEL_PATTERN = re.compile(r'pixel \s* \( \s* (\d+\%?) \s*,\s* (\d+\%?)  (?: \s*,\s* (\w+))? (?: \s*,\s* (\w+))? \s* \)', re.RegexFlag.X)

class position :
    def __init__(self, pos_str : str ) -> None :
        self.pos_str = pos_str
        self._valid = False
        self._width = ''
        self._height = ''
        self._ref = ''
        self._side = ''
        self._anchor : Tuple[str, str] = ('min', 'min')

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
            self._ref = 'output'
            self._valid = True

    def _parse_function(self) :

        if self._parse_pixel() :
            return
        
        m = POS_PATTERN.fullmatch(self.pos_str)
        if not m :
            raise ValueError(f"Invalid function position string: {self.pos_str}")

        ref, width, height, side = m.groups()

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
        self._ref = ref
        self._valid = True
        self._side = side or ''

    def _parse_pixel(self) :
        m = PIXEL_PATTERN.fullmatch(self.pos_str)
        if not m :
            return False

        width, height = m.groups()[0:2]
        if len(m.groups()) == 3 :
            self._anchor = (m.groups()[2], 'mid')
        elif len(m.groups()) == 4 :
            self._anchor = (m.groups()[2], m.groups()[3])

        self._width = width
        self._height = height
        self._ref = 'output'
        self._side = 'pixel'

        self._valid = True
        return True

    def valid(self) -> bool:
        return self._valid
    
    @property
    def w(self) -> str :
        return self._width

    @property
    def h(self) -> str :
        return self._height
    
