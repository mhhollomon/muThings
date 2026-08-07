from dataclasses import dataclass
from typing import Any, List

from .position import position, geom

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

class PathSetting(Settings) :
    def path_valid(self) -> bool :
        path = getattr(self, 'path')
        return path is not None and path != ''

@dataclass
class GlobalSettings(Settings) :
    gutter : int
    font : str

@dataclass
class OutputSettings(PathSetting) :
    path : str
    size : geom
    color : str
    background : str

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

@dataclass
class CoverSettings(PathSetting) :
    path : str
    align : str
    crop : str
    fit : str
    color : str | None # This is a convenience attribute
    border : BorderSettings
    margin : int

@dataclass
class GraphicSettings(PathSetting) :
    path : str
    size : int
    mask : str
    position : position

@ dataclass
class StrokeSettings(Settings) :
    color : str
    width : int

    def exists(self) -> bool :
        return self.width > 0

@dataclass 
class TextSettings(Settings) :
    text : str
    size : int
    font : str
    position : position
    fill : str
    stroke : StrokeSettings
    rotation : int

    def has_text(self) -> bool :
        return self.text is not None and self.text != ''

    def validate(self) :
        if self.rotation not in (-90, 0, 90, 180) :
            raise ValueError(f"Invalid rotation {self.rotation} for text ")
        if self.size is None or self.size < 1 :
            raise ValueError(f"Invalid size '{self.size}' for text")


@dataclass
class Config(Settings) :
    globals : GlobalSettings
    output  : OutputSettings
    cover   : CoverSettings
    logo    : GraphicSettings
    title   : TextSettings
    album   : TextSettings
    text_blocks  : List[TextSettings]
