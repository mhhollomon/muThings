from dataclasses import dataclass, field
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

    def print(self, prefix : str = '') :
        print(f"{prefix}{str(self)}")


# -------------------------------------------------------------------------

class PathSetting(Settings) :
    def path_valid(self) -> bool :
        path = getattr(self, 'path')
        return path is not None and path != ''

# -------------------------------------------------------------------------

@dataclass
class GlobalSettings(Settings) :
    gutter : int = 10
    font : str = ''
    fill : str = '"white"'

    def print(self, prefix : str = '') :
        print(f"{prefix}GlobalSettings {{")
        new_prefix = prefix + '  '
        print(f"{new_prefix}gutter={self.gutter}")
        print(f"{new_prefix}font={self.font}")
        print(f"{new_prefix}fill={self.fill}")
        print(f"{prefix}}}")

# -------------------------------------------------------------------------

@dataclass
class OutputSettings(PathSetting) :
    path : str = ''
    size : sizet = field(default_factory=lambda :sizet(1920, 1080))
    color : str = '"black"'
    background : str = ''
    margin : int = 0
    border : 'BorderSettings' = field(default_factory=lambda :BorderSettings())

    def print(self, prefix: str = ''):
        print(f"{prefix}OutputSettings {{")
        new_prefix = prefix + '  '
        print(f"{new_prefix}path={self.path}")
        print(f"{new_prefix}size={self.size}")
        print(f"{new_prefix}color={self.color}")
        print(f"{new_prefix}background={self.background}")
        print(f"{new_prefix}margin={self.margin}")
        self.border.print(new_prefix)
        print(f"{prefix}}}")

# -------------------------------------------------------------------------

class WidthSettings(Settings) :
    l : int = -1
    r : int = -1
    t : int = -1
    b : int = -1

    def __init__(self, l : int = -1, r : int = -1, t : int = -1, b : int = -1) :
        self.l = l
        self.r = r
        self.t = t
        self.b = b

    def is_zero(self) :
        return self.l < 1 and self.r < 1 and self.t < 1 and self.b < 1

    def merge(self, other : 'WidthSettings') -> 'WidthSettings' :
        for attr in ('l', 'r', 't', 'b') :
            value = getattr(other, attr)
            if value > 0 :
                setattr(self, attr, value)
            elif value == 0 :
                setattr(self, attr, -1)

        return self

    def validate(self) -> bool :
        for attr in ('l', 'r', 't', 'b') :
            value = getattr(self, attr)
            if value < -1 :
                raise ValueError(f"Invalid width '{value}' for side '{attr}'")
        return True

    def __str__(self) :
        string = "width {"
        settings = [f"{attr}={getattr(self, attr)}" for attr in ('l', 'r', 't', 'b') if getattr(self, attr) > 0]
        string += ', '.join(settings)
        string += '}'
        return string


# -------------------------------------------------------------------------

@dataclass
class BorderSettings(Settings) :
    color : str | None = None
    width : WidthSettings | None = None

    def exists(self) -> bool :
        return self.width is not None and not self.width.is_zero()

    def validate(self) -> bool :
        # if there is a width we have to have a color
        if self.width is not None :
            #self.width.validate()
            if self.color is None :
                raise ValueError("Border has width but no color")

        return True
        
    def merge(self, other) :
        if other.color is not None :
            self.color = other.color
        if other.width is not None :
            if self.width is None :
                self.width = other.width
            else :
                self.width.merge(other.width)

    def print(self, prefix : str = '') :
        print(f"{prefix}border {{")
        new_prefix = prefix + '  '
        if self.color is not None :
            print(f"{new_prefix}color={self.color}")
        if self.width is not None :
            self.width.print(new_prefix)
        print(f"{prefix}}}")

    def __str__(self) :
        string = "border {"
        if self.color is not None :
            string += f"color={self.color}"
        if self.width is not None :
            string += f", {self.width}"
        string += '}'
        return string


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
    name : str | None
    path : str
    size : int
    mask : str
    position : position

    def named(self) -> bool :
        return self.name is not None and self.name != ''

    def merge(self, other : Any) :
        if isinstance(other, GraphicSettings) :
            raise ValueError("Cannot merge GraphicSettings with GraphicSettings (yet)")
        
        logger.debug(f"GraphicSettings.merge: {self.name} input = {other}")
        other = NoneDict(other)
        self.override('name', other['name'])
        self.override('path', other['path'])
        self.override('size', other['size'])
        self.override('mask', other['mask'])
        self.override('position', other['position'])
        logger.debug(f"GraphicSettings.merge: {self.name} final = {self}")

    def validate(self) -> bool :
        return self.size > 0

# -------------------------------------------------------------------------

@ dataclass
class StrokeSettings(Settings) :
    color : str | None = None
    width : int | None = None


    def exists(self) -> bool :
        return self.width is not None

    def merge(self, other) :
        if other.color is not None :
            self.color = other.color
        if other.width is not None :
            self.width = other.width

    def validate(self) -> bool :
        if self.width is not None and self.width < 0 :
            raise ValueError("Stroke width cannot be negative")
        return True

    def __str__(self) :
        string = "stroke {"
        if self.color is not None :
            string += f"color={self.color}"
        if self.width is not None :
            string += f", width={self.width}"
        string += '}'
        return string


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
        if isinstance(new_block, TextSettings) :
            raise ValueError("Cannot merge TextSettings with TextSettings (yet)")
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
class ConfigOld(Settings) :
    globals : GlobalSettings = field(default_factory=GlobalSettings)
    output  : OutputSettings = field(default_factory=OutputSettings)
    cover   : CoverSettings = field(default_factory=lambda :CoverSettings('', 'min', 'min', 'square', None, BorderSettings('#000000', None), margin=0))
    logo    : GraphicSettings = field(default_factory=lambda :GraphicSettings('', '', 10, 'black', position('right-bottom')))
    elements  : List[TextSettings | GraphicSettings] = field(default_factory=list)

    def print(self, prefix : str = '') :
        print(f"{prefix}Config:")
        prefix += '  '
        self.globals.print(prefix)
        self.output.print(prefix)
        self.cover.print(prefix)
        self.logo.print(prefix)
        for e in self.elements :
            e.print(prefix)
