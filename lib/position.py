
from dataclasses import dataclass
import re
from typing import Tuple

import logging
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
        self._anchor = ('min', 'min')

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
    

    def _pixel_offsets(self, output_rect : rectangle, elem_size : geometry, gutter : int) -> Tuple[int, int] :
        if '%' in self._width :
            w_offset = int(self._width[:-1]) * output_rect.extent.width // 100
        else :
            w_offset = int(self._width)

        if '%' in self._height :
            h_offset = int(self._height[:-1]) * output_rect.extent.height // 100
        else :
            h_offset = int(self._height)

        # h_offset and w_offset are where our anchor should be.
        # Now, convert the offsets to the top left of the element.
        if self._anchor[0] == 'max' :
            w_offset -=  elem_size.width 
        elif self._anchor[0] == 'mid' :
            w_offset -= elem_size.width // 2
        elif self._anchor[0] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {self._anchor[0]}")

        logger.debug(f"Anchor offset = {w_offset}, {h_offset}")

        if self._anchor[1] == 'max' :
            h_offset -= elem_size.height
        elif self._anchor[1] == 'mid' :
            h_offset -= elem_size.height // 2
        elif self._anchor[1] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {self._anchor[1]}")

        logger.debug(f"element offset = {w_offset}, {h_offset}")

        # Check to make sure the element is fully in the output rec (if possible).
        if w_offset > output_rect.extent.width - elem_size.width - gutter:
            w_offset = output_rect.extent.width - elem_size.width - gutter

        if w_offset < gutter:
            w_offset = gutter

        if h_offset > output_rect.extent.height - elem_size.height - gutter:
            h_offset = output_rect.extent.height - elem_size.height - gutter

        if h_offset < gutter:
            h_offset = gutter

        logger.debug(f"final offset: {w_offset}, {h_offset}")
        return w_offset, h_offset

    
    def offsets(self, output_rect : rectangle, cover_rect : rectangle, border_rect : rectangle, elem_size : geometry, gutter : int) -> Tuple[int, int] :
        if not self.valid():
            raise ValueError("Position is not valid")

        logger.debug(f"""Position Inputs :
 position = {self.pos_str}
 output_rec = {output_rect.to_tuple()},
 cover_rect = {cover_rect.to_tuple()},
 border_rect = {border_rect.to_tuple()},
 elem_size = {elem_size.to_tuple()},
 gutter = {gutter}"""
    )
        
        if self._side == 'pixel' :
            return self._pixel_offsets(output_rect, elem_size, gutter)
        
        if self._ref == 'output' :
            ref_rect = output_rect
        elif self._ref == 'cover' :
            ref_rect = cover_rect
            gutter = 0
        elif self._ref == 'border' :
            gutter = 0
            ref_rect = border_rect.copy()
            if self._side == 'left' :
                ref_rect.extent.width = cover_rect.start.width - ref_rect.start.width
            elif self._side == 'right' :
                ref_rect.start.width = cover_rect.start.width + cover_rect.extent.width
                ref_rect.extent.width = (ref_rect.extent.width - cover_rect.extent.width) // 2
            elif self._side == 'top' :
                ref_rect.extent.height = cover_rect.start.height - ref_rect.start.height
            elif self._side == 'bottom' :
                ref_rect.start.height = cover_rect.start.height + cover_rect.extent.height
                ref_rect.extent.height = ref_rect.extent.height - ref_rect.start.height

        logger.debug(f"Updated ref_rect = {ref_rect.to_tuple()}")
        
        # Calculate the offset
        if self.w == 'min':
            width_offset = gutter
        elif self.w == 'mid':
            width_offset = (ref_rect.extent.width - elem_size.width) // 2
        elif self.w == 'max':
            width_offset = ref_rect.extent.width - elem_size.width - gutter

        if self.h == 'min':
            height_offset = gutter
        elif self.h == 'mid':
            height_offset = (ref_rect.extent.height - elem_size.height) // 2
        elif self.h == 'max':
            height_offset = ref_rect.extent.height - elem_size.height - gutter

        logger.debug(f"Offsets = ({width_offset}, {height_offset})")

        # Match the references position
        width_offset += ref_rect.start.width
        height_offset += ref_rect.start.height

        logger.debug(f"Final offsets = ({width_offset}, {height_offset})")

        return (width_offset, height_offset)

