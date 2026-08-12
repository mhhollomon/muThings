from typing import Any, NamedTuple

from lark import Lark, Transformer, v_args, Token, logger as lark_logger
import logging

lark_logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

from .settings import *

from pathlib import Path

def _get_default_font() :
    #import sys
    import platform
    #print(f"==== sys.platform: {sys.platform}")
    #print(f"==== platform: {platform.platform()}")
    if 'WSL2' in platform.platform():
        return '/mnt/c/Windows/Fonts/arial.ttf'
    else:
        return 'Arial'


class OptionTuple(NamedTuple) :
    name : str
    value : Any

class DefaultOption(NamedTuple) :
    name : str
    value : Any

#--------------------------------------------------------------------------

class Configuration(Transformer) :
    context : Path
    defaults : DefaultSettings
    output  : OutputSettings
    cover   : CoverSettings | None
    elements  : List[TextSettings | ImageSettings]

    def __init__(self, config_file : str, toplevel : bool = True) :
        super().__init__()
        self.toplevel = toplevel
        self._config_file = Path(config_file)

        self.context = self._config_file.parent
        self.defaults = DefaultSettings(_get_default_font(), '"white"')
        # output can't (ultimately) be None. So I don't want to pollute the type system.
        self.output   = None # type: ignore
        self.cover    = None
        self.elements = []

    def read_config(self) -> None :
        grammar = Path(__file__).parent / 'config.lark'

        with open(self._config_file, 'r') as f :
            text = f.read()
        parser = Lark(grammar.read_text(), parser='lalr', debug=True, start='mupic_config_file', maybe_placeholders=True, strict=True)

        tree = parser.parse(text)
        _ = self.transform(tree)

        if self.toplevel :
            self.validate()

    def print(self, prefix : str = '') :
        print(f"{prefix}Config:")
        prefix += '  '
        self.defaults.print(prefix)
        if self.output is not None :
            self.output.print(prefix)
        if self.cover is not None :
            self.cover.print(prefix)
        for e in self.elements :
            e.print(prefix)

    def validate(self) -> None :
        if self.output is None :
            raise ValueError("No output specified")
        else :
            self.output.validate()

    #--------------------------------------------
    # Lark Transform routines
    #--------------------------------------------

    def __default__(self, data, children, meta) :
        if data.endswith('_option') :
            if data.endswith('_int_option') :
                data = data[:-11]
                logger.debug(f"==== int option default handling: {data} = {children[0]}")
                return OptionTuple(data, int(children[0].value))
            else :
                data = data[:-7]
                logger.debug(f"==== option default handling: {data} = {children[0]}")
                return OptionTuple(data, 
                    children[0].value if isinstance(children[0], Token) else children[0])
        return super().__default__(data, children, meta)

    @v_args(inline=True)
    def default_stmt(self, name : Token, value : Token) :
        name = name.value
        if hasattr(self.defaults, name) :
            setattr(self.defaults, name, value.value)
            return DefaultOption(name, value.value)
        else :
            raise ValueError(f"Invalid default statement: {name}")

    @v_args(inline=True)
    def size_2d_option(self, value : Token) :
        return OptionTuple('size', sizet(value.value))
    
    @v_args(inline=True)
    def one_side(self, side : Token, value : Token) :
        return OptionTuple(side.value, value.value)
        

    def width_spec(self, children) -> WidthSettings :
        if len(children) == 1 and isinstance(children[0], Token) :
            size = int(children[0].value)
            return WidthSettings(size, size, size, size)
        settings = {}
        for child in children :
            if isinstance(child, OptionTuple) :
                settings[child.name] = int(child.value)
            else :
                raise ValueError(f"Invalid width spec: {child}")
        return WidthSettings(**settings)

    def border_spec(self, children) -> BorderSettings :
        settings = BorderSettings()
        for child in children :
            if isinstance(child, OptionTuple) :
                if settings.color is not None :
                    raise ValueError(f"Invalid border spec - Multiple colors: {child}")
                settings.color = child.value
            elif isinstance(child, WidthSettings) :
                if settings.width is not None :
                    raise ValueError(f"Invalid border spec - Multiple widths: {child}")
                settings.width = child
            else :
                raise ValueError(f"Invalid border spec: {child}")

        return settings

    def stroke_spec(self, children) -> StrokeSettings :
        settings = StrokeSettings()
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name == 'color' :
                    if settings.color is not None :
                        raise ValueError(f"Invalid stroke spec - Multiple colors: {child}")
                    settings.color = child.value
                elif child.name == 'width' :
                    if settings.width is not None :
                        raise ValueError(f"Invalid stroke spec - Multiple widths: {child}")
                    settings.width = child.value
                else :
                    raise ValueError(f"Invalid stroke spec: {child}")
            else :
                raise ValueError(f"Invalid stroke spec: {child}")

        return settings

    def output_stmt(self, children) :
        if self.output is None :
            self.output = OutputSettings()
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name in ('name', 'path', 'size', 'color', 'background', 'margin') :
                    setattr(self.output, child.name, child.value)
                else :
                    raise ValueError(f"Invalid output statement: {child}")
            elif isinstance(child, BorderSettings) :
                self.output.border = child
            else :
                raise ValueError(f"Invalid output statement: {child}")

    def cover_stmt(self, children) :
        if self.cover is None :
            self.cover = CoverSettings(align='min', fit='square', crop='mid')
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name in ('path', 'align', 'fit', 'crop', 'margin') :
                    setattr(self.cover, child.name, child.value)
                else :
                    raise ValueError(f"Invalid cover statement: {child}")
            elif isinstance(child, BorderSettings) :
                self.cover.border = child
            else :
                raise ValueError(f"Invalid cover statement: {child}")

    def image_stmt(self, children) :
        name = children[0].value
        new_image = ImageSettings(name=name, path = '',size=0, mask='auto',position=position(''))
        self.elements.append(new_image)

        for child in children[1:] :
            if isinstance(child, OptionTuple) :
                if child.name in ('path', 'size', 'mask', 'position', 'margin', 'color') :
                    setattr(new_image, child.name, child.value)
                else :
                    raise ValueError(f"Invalid image statement: {child}")
            elif isinstance(child, BorderSettings) :
                new_image.border = child
            else :
                raise ValueError(f"Invalid image statement: {child}")

