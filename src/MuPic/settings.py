from dataclasses import dataclass
from typing import Any, List

from .position import position
from .geometry import sizet

from .none_dict import NoneDict

import logging
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# BASE CLASS Settings
# -------------------------------------------------------------------------
class Settings :

    def valid_value(self, value : Any) -> bool :

        if value is None :
            return False
        
        if isinstance(value, str) :
            return value.strip() != ''
        
        try :
            return value.valid()
        except AttributeError :
            pass

        return True
    
    def valid_attr(self, key : str) -> bool :
        return self.valid_value(getattr(self, key))
    
    def override(self, key : str, new_value : Any) :
        """Update the value of the attribute if the NEW value is NOT None."""
        if self.valid_value(new_value) :
            setattr(self, key, new_value)

    def default(self, key : str, new_value : Any) :
        """Update the value of the attribute if the OLD value is None."""
        old_value = getattr(self, key)
        if not self.valid_value(old_value) :
            setattr(self, key, new_value)

# -------------------------------------------------------------------------

class PathSetting(Settings) :
    def path_valid(self) -> bool :
        path = getattr(self, 'path')
        return path is not None and path != ''

# -------------------------------------------------------------------------

@dataclass
class GlobalSettings(Settings) :
    gutter : int
    font : str

# -------------------------------------------------------------------------

@dataclass
class OutputSettings(PathSetting) :
    path : str
    size : sizet
    color : str
    background : str

# -------------------------------------------------------------------------

@dataclass
class BorderSettings(Settings) :
    color : str
    width : int
    sides : str = 'lrtb'

    def exists(self) -> bool :
        return self.width > 0

    def validate(self) -> bool :
        if self.width < 0 :
            raise ValueError("Border width cannot be negative")

        for side in self.sides.lower() :
            if side not in ('l', 'r', 't', 'b') :
                raise ValueError(f"Invalid border side: {side}")

        return True

# -------------------------------------------------------------------------

@dataclass
class CoverSettings(PathSetting) :
    path : str
    align : str
    crop : str
    fit : str
    color : str | None # This is a convenience attribute
    border : BorderSettings
    margin : int

# -------------------------------------------------------------------------

@dataclass
class GraphicSettings(PathSetting) :
    path : str
    size : int
    mask : str
    position : position

# -------------------------------------------------------------------------

@ dataclass
class StrokeSettings(Settings) :
    color : str
    width : int

    def __post_init__(self) :
        self.width = int(self.width)

    def exists(self) -> bool :
        return self.width > 0

    def merge(self, new_block : Any) :
        new_block = NoneDict(new_block)
        self.override('color', new_block['color'])
        self.override('width', int(new_block['width'] or 0))

    def validate(self) :
        if self.width < 0 :
            raise ValueError("Stroke width cannot be negative")

# -------------------------------------------------------------------------

@dataclass 
class TextSettings(Settings) :
    name : str
    text : str
    size : int
    font : str
    position : position
    fill : str
    stroke : StrokeSettings
    rotation : int

    @classmethod
    def from_dict(cls, d : dict) :
        return TextSettings(**d)

    def has_text(self) -> bool :
        return self.text is not None and self.text != ''

    def named(self) -> bool :
        return self.name is not None and self.name != ''

    def merge(self, new_block : Any) :
        logger.debug(f"TextSettings.merge: {self.name} input = {new_block}")
        new_block = NoneDict(new_block)
        self.override('text', new_block['text'])
        self.override('size', new_block['size'])
        self.override('font', new_block['font'])
        self.override('position', new_block['position'])
        self.override('fill', new_block['fill'])
        self.override('rotation', new_block['rotation'])

        self.stroke.merge(new_block['stroke'])
        logger.debug(f"TextSettings.merge: {self.name} final = {self}")

    def validate(self) -> bool:
        if self.rotation not in (-90, 0, 90, 180) :
            raise ValueError(f"Invalid rotation '{self.rotation}' for text ")
        if self.size is None or self.size < 1 :
            raise ValueError(f"Invalid size '{self.size}' for text")

        self.stroke.validate()

        return True

# -------------------------------------------------------------------------
# CONFIG CLASS
# -------------------------------------------------------------------------

@dataclass
class Config(Settings) :
    globals : GlobalSettings
    output  : OutputSettings
    cover   : CoverSettings
    logo    : GraphicSettings
    text_blocks  : List[TextSettings]
