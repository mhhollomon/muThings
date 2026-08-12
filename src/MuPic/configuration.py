from typing import Any, NamedTuple

from lark import Transformer, v_args, Token

from .settings import *

from pathlib import Path

class OptionTuple(NamedTuple) :
    name : str
    value : Any

class DefaultOption(NamedTuple) :
    name : str
    value : Any

class Configuration(Transformer) :
    def __init__(self, config_file : str) :
        super().__init__()
        self.config = ConfigOld()
        self.config_file = Path(config_file)
        self.context = self.config_file.parent

    def __default__(self, data, children, meta) :
        if data.endswith('_option') :
            data = data[:-7]
            print(f"==== {data} = {children[0]}")
            return OptionTuple(data, 
                children[0].value if isinstance(children[0], Token) else children[0])
        return super().__default__(data, children, meta)

    @v_args(inline=True)
    def default_stmt(self, name : Token, value : Token) :
        name = name.value
        if hasattr(self.config.globals, name) :
            setattr(self.config.globals, name, value.value)
            return DefaultOption(name, value.value)
        else :
            raise ValueError(f"Invalid default statement: {name}")

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
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name == 'path' :
                    self.config.output.path = child.value
                elif child.name == 'size' :
                    self.config.output.size = child.value
                elif child.name == 'color' :
                    self.config.output.color = child.value
                elif child.name == 'background' :
                    self.config.output.background = child.value
                elif child.name == 'margin' :
                    self.config.output.margin = child.value
                else :
                    raise ValueError(f"Invalid output statement: {child}")
            elif isinstance(child, BorderSettings) :
                self.config.output.border = child
            else :
                raise ValueError(f"Invalid output statement: {child}")

